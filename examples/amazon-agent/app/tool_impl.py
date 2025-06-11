import logging
from browser_use.browser.context import BrowserContext
from  .utils import review_checkout_card_empty_delivery, check_browser_current_state, is_showing_captcha, IncrementID, browse, normalize_url
import json
import asyncio
from .config import AMAZON_URL
import urllib.parse

logger = logging.getLogger()

async def sign_in(ctx: BrowserContext, **args):
    page = await ctx.get_current_page()
    current_url = page.url
    logger.info(f"Current URL: {current_url}")
    if 'amazon.com/ap/signin' in current_url:
        input_element = await page.query_selector('#ap_email_login')
        if input_element:
            value = await input_element.input_value()
            if not value.strip():
                raise Exception("Login is required to continue.")
        else:
            raise Exception("Login is required to continue.")

async def search_products(ctx: BrowserContext, **args):
    logger.info(f"Search products called with {args}")
    query = args.get("query")
    if not query:
        yield json.dumps({
            "status": "error",
            "message": "Query is required to continue."
        })
        return
    
    if await is_showing_captcha(ctx):
        yield json.dumps({
            "status": "error",
            "message": "CAPTCHA challenge detected, manual intervention required."
        })
        return
    
    page = await ctx.get_current_page()
    # get origin location
    current_url = page.url
    origin = current_url.split('/')[0] + '//' + current_url.split('/')[2]
    logger.info(f"Origin location: {origin}")
    try:
        url = f"{origin}/s?k={urllib.parse.quote(query)}"
        await page.goto(url)
        await page.wait_for_load_state('domcontentloaded')
        await page.query_selector('[role="listitem"].s-result-item')
    except Exception as e:
        yield json.dumps({
            "status": "error",
            "message": f"Failed to search products: {e}"
        })
        return
    
    # Check for country redirect popup
    redirect_overlay = await page.query_selector('#redir-overlay')
    if redirect_overlay:
        logger.info("Country redirect popup detected")
        # Get the current URL to determine which Amazon site we're on
        current_url = page.url
        amazon_domain = current_url.split('/')[2]
        
        # Get the stay and go buttons
        stay_button = await page.query_selector('#redir-stay-at-www')
        go_button = await page.query_selector('#redir-go-to-site')
        
        if stay_button and go_button:
            # Get the text content to show user the options
            stay_text = await stay_button.text_content()
            go_text = await go_button.text_content()
            
            # Ask user to confirm which site to use
            yield json.dumps({
                "status": "redirect_confirmation_needed",
                "message": f"Amazon is asking to confirm which site to use. Current site: {amazon_domain}",
                "options": {
                    "stay": stay_text.strip(),
                    "go": go_text.strip()
                }
            })
            return

    search_results = await page.query_selector_all('[role="listitem"].s-result-item')
    logger.info(f"Search results count: {len(search_results)}")

    products = []
    if len(search_results) == 0:
        gen_id = IncrementID()

        task = 'Strictly follow the instructions below:\n'
        task += f'{gen_id()}. Search products by {query}.\n'
        task += f'{gen_id()}. Click button search.\n'
        task += f'{gen_id()}. Get list products from search results.\n'
        task += f"{gen_id()}. Return the list products in JSON format. The JSON format should be like this: [{{'product_index': 0, 'name': 'Product Name', 'price': 'Price', 'rating': 'Rating', 'reviews': 'Reviews', 'prime': 'Prime', 'link': 'Product Link'}}, ...]\n"
        
        logger.info(f"Browse task: {task}")
        msg = await browse(task, ctx, 10)
        logger.info(f"Search results from browser: {msg}")
        if isinstance(msg, str):
            try:
                product_data = json.loads(msg)
                if isinstance(product_data, dict):
                    products.append(product_data)
            except json.JSONDecodeError:
                pass
        yield json.dumps({"status": "success", "products": products}, ensure_ascii=False, indent=2)
    
    
    for idx, result in enumerate(search_results[:10]):
        # Name
        name = None
        name_el = await result.query_selector('h2 span')
        if name_el:
            name = (await name_el.text_content()).strip()

        # Price
        price = None
        price_el = await result.query_selector('.a-price .a-offscreen')
        if price_el:
            price = (await price_el.text_content()).strip()

        # Rating
        rating = None
        rating_el = await result.query_selector('.a-icon-alt')
        if rating_el:
            rating_text = (await rating_el.text_content()).strip()
            try:
                rating = float(rating_text.split(' out of')[0])
            except Exception:
                rating = None

        # Reviews
        reviews = None
        reviews_el = await result.query_selector('a[href*="#customerReviews"] span')
        if reviews_el:
            reviews = (await reviews_el.text_content()).strip().replace('(', '').replace(')', '')

        # Prime
        prime = False
        prime_el = await result.query_selector('.a-icon-prime')
        if prime_el:
            prime = True

        # Link
        link = None
        link_el = await result.query_selector('a.a-link-normal.s-no-outline, h2 a.a-link-normal, a.a-link-normal.s-line-clamp-2')
        if link_el:
            href = await link_el.get_attribute('href')
            if href:
                # Handle affiliate links
                if href.startswith('/sspa/click'):
                    parsed = urllib.parse.urlparse(href)
                    qs = urllib.parse.parse_qs(parsed.query)
                    url_param = qs.get('url', [None])[0]
                    if url_param:
                        real_url = urllib.parse.unquote(url_param)
                        # Remove query string and fragment from real_url
                        real_url = urllib.parse.urlunparse(urllib.parse.urlparse(real_url)._replace(query='', fragment=''))
                        # If the real_url is a relative path, prepend AMAZON_URL
                        if real_url.startswith('/'):
                            # If the URL is relative (starts with /), prepend the origin
                            link = f"{origin}{real_url}"
                        else:
                            # If the URL is absolute, still combine with origin to ensure consistent domain
                            parsed_real_url = urllib.parse.urlparse(real_url)
                            link = f"{origin}{parsed_real_url.path}"
                            if parsed_real_url.query:
                                link += f"?{parsed_real_url.query}"
                    else:
                        link = f"{origin}{href.split('?')[0]}"
                else:
                    link = f"{origin}{href.split('?')[0]}"

        # Only add if name and link exist
        if name and link:
            products.append({
                "product_index": idx,
                "name": name,
                "price": price,
                "rating": rating,
                "reviews": reviews,
                "prime": prime,
                "link": link
            })

    yield json.dumps({"status": "success", "products": products}, ensure_ascii=False, indent=2)

async def get_product_detail(ctx: BrowserContext, **args):
    page = await ctx.get_current_page()
    link = args.get("link")
    if not link:
        yield json.dumps({"error": "link is required"})
        return
    if normalize_url(page.url) != normalize_url(link):
        await page.goto(link)
    # Wait for the product title to appear (as a proxy for page load)
    try:
        await page.wait_for_load_state('domcontentloaded')
        await page.query_selector('#productTitle')

    except Exception:
        try:
            title_el = await page.query_selector('h1')
            if title_el:
                title = (await title_el.text_content()).strip()
            else:
                yield json.dumps({"error": "Failed to load product detail page or selector not found."})
                return
        except Exception:
            yield json.dumps({"error": "Failed to load product detail page or selector not found."})
            return

    # Title
    title = None
    title_el = await page.query_selector('#productTitle, h1')
    if title_el:
        title = (await title_el.text_content()).strip()

    # Price
    price = None
    price_selectors = ['#priceblock_ourprice', '#priceblock_dealprice', '.a-price .a-offscreen']
    for sel in price_selectors:
        price_el = await page.query_selector(sel)
        if price_el:
            price = (await price_el.text_content()).strip()
            if price:
                break

    # Rating
    rating = None
    rating_el = await page.query_selector('.a-icon-star span.a-icon-alt')
    if rating_el:
        rating_text = (await rating_el.text_content()).strip()
        try:
            rating = float(rating_text.split(' out of')[0])
        except Exception:
            rating = rating_text

    # Number of reviews
    reviews = None
    reviews_el = await page.query_selector('#acrCustomerReviewText')
    if reviews_el:
        reviews = (await reviews_el.text_content()).strip()

    # Bullet points/features
    features = []
    feature_els = await page.query_selector_all('#feature-bullets ul li span')
    for el in feature_els:
        text = (await el.text_content()).strip()
        if text:
            features.append(text)
            
    # Description
    description = None
    description_el = await page.query_selector('#productDescription_feature_div p')
    if description_el:
        description = (await description_el.text_content()).strip()
        
    # Delivery
    delivery = None
    delivery_time = None
    delivery_cutoff = None
    delivery_price = None

    delivery_el = await page.query_selector('span[data-csa-c-delivery-type="Delivery"]')
    if delivery_el:
        # Try to get delivery time from attribute
        delivery_time = await delivery_el.get_attribute('data-csa-c-delivery-time')
        delivery_cutoff = await delivery_el.get_attribute('data-csa-c-delivery-cutoff')
        delivery_price = await delivery_el.get_attribute('data-csa-c-delivery-price')
        # Fallback: try to get visible text if attribute is missing
        if not delivery_time:
            # Try to get the text from the bold span inside
            bold_time_el = await delivery_el.query_selector('span.a-text-bold')
            if bold_time_el:
                delivery_time = (await bold_time_el.text_content()).strip()
        if not delivery_cutoff:
            cutoff_el = await delivery_el.query_selector('#ftCountdown')
            if cutoff_el:
                delivery_cutoff = (await cutoff_el.text_content()).strip()
        # Compose delivery string
        delivery = {
            "time": delivery_time,
            "cutoff": delivery_cutoff,
            "price": delivery_price
        }

    product_detail = {
        "title": title,
        "price": price,
        "rating": rating,
        "reviews": reviews,
        "features": features,
        "description": description,
        "url": link,
        "delivery": delivery
    }

    yield json.dumps({"status": "success", "data": product_detail}, ensure_ascii=False, indent=2)

async def check_out(ctx: BrowserContext, **args):
    page = await ctx.get_current_page()
    if normalize_url(page.url) != normalize_url(f"{AMAZON_URL}/cart"):
        await page.goto(f"{AMAZON_URL}/cart")
        await asyncio.sleep(2)

    # Click on the "Proceed to checkout" button
    await page.wait_for_selector("input[name='proceedToRetailCheckout']", state='visible')
    checkout_button = await page.query_selector("input[name='proceedToRetailCheckout']")
    if checkout_button:
        await checkout_button.click()
        logger.info("Checkout button clicked, waiting for the next page to load...")
        await asyncio.sleep(2)

        await check_browser_current_state(ctx)

        await asyncio.sleep(3)

        # Ensure we are on the checkout page
        logger.info(f"Current page URL after clicking checkout: {page.url}")
        logger.info(f"is /checkout: {'/checkout' in page.url}")

        # check if url contain '/checkout'
        if page.url and '/checkout' in page.url:
        # check if Prime sign up is showing, if so, click on the "No thanks" button a.prime-decline-button
            prime_sign_up = await page.query_selector('a#prime-decline-button')
            logger.info(f"Prime sign up button found: {prime_sign_up}")
            if prime_sign_up:
                logger.info("Prime sign up detected, clicking 'No thanks' button.")
                await prime_sign_up.click()
                await asyncio.sleep(2)

        # check for 
        await review_checkout_card_empty_delivery(ctx)

        # Read context from #widget-purchaseConfirmationDetails and response to the user
        await page.wait_for_selector("#widget-purchaseConfirmationDetails h4", state='visible')
        confirmation_details = await page.query_selector("#widget-purchaseConfirmationDetails h4")

        if confirmation_details:
            confirmation_details_status = await confirmation_details.text_content()
            confirmation_details_content_text = await confirmation_details.text_content()

            yield f"Checkout completed. Confirmation details: {confirmation_details_status}, {confirmation_details_content_text}"
    else:
        yield "Checkout button not found."
        return
    
async def go_to_cart(ctx: BrowserContext, **args):
    page = await ctx.get_current_page()
    if normalize_url(page.url) != normalize_url(f"{AMAZON_URL}/cart"):
        await page.goto(f"{AMAZON_URL}/cart")
        await page.wait_for_load_state('domcontentloaded')

    try:
        await page.query_selector('#activeCartViewForm')
        cart_items = await page.query_selector_all('#activeCartViewForm .sc-list-item')
        cart_contents = []

        for item in cart_items:
            # Title
            title = None
            title_el = await item.query_selector('.sc-product-title')
            if title_el:
                title = (await title_el.text_content()).strip()

            # Price
            price = None
            price_el = await item.query_selector('.a-price.apex-price-to-pay-value')
            if price_el:
                price_span = await price_el.query_selector('.a-offscreen')
                if price_span:
                    price = (await price_span.text_content()).strip()

            # Quantity
            quantity = 1
            quantity_el = await item.query_selector('div[role="spinbutton"]')
            if quantity_el:
                try:
                    quantity_val = await quantity_el.get_attribute('aria-valuenow')
                    if quantity_val:
                        quantity = int(quantity_val)
                except Exception:
                    pass
            else:
                quantity_span = await item.query_selector('span[data-a-selector="value"]')
                if quantity_span:
                    try:
                        quantity_val = await quantity_span.text_content()
                        if quantity_val:
                            quantity = int(quantity_val)
                    except Exception:
                        pass


            # Remove button selector (input[name^="submit.delete-active."])
            remove_btn = await item.query_selector('input[name^="submit.delete-active."]')
            remove_button_selector = None
            if remove_btn:
                btn_name = await remove_btn.get_attribute('name')
                if btn_name:
                    remove_button_selector = f'input[name="{btn_name}"]'
                else:
                    remove_button_selector = 'input[name^="submit.delete-active."]'

            # Edit button selector (stepper or quantityBox)
            # Prefer stepper increment/decrement buttons if available, else fallback to quantityBox input
            edit_button_selector = None
            increment_btn = await item.query_selector('button[data-action="a-stepper-increment"]')
            decrement_btn = await item.query_selector('button[data-action="a-stepper-decrement"]')
            quantity_box = await item.query_selector('input[name="quantityBox"]')
            if increment_btn:
                edit_button_selector = 'button[data-action="a-stepper-increment"]'
            elif decrement_btn:
                edit_button_selector = 'button[data-action="a-stepper-decrement"]'
            elif quantity_box:
                edit_button_selector = 'input[name="quantityBox"]'

            cart_contents.append({
                "title": title,
                "price": price,
                "quantity": quantity,
                "remove_button_selector": remove_button_selector,
                "edit_button_selector": edit_button_selector,
                "increment_quantity_selector": 'button[data-action="a-stepper-increment"]' if increment_btn else None,
                "decrement_quantity_selector": 'button[data-action="a-stepper-decrement"]' if decrement_btn else None
            })
        logger.info(f"Cart contents: {cart_contents}")
        yield json.dumps({"status": "success", "cart_contents": cart_contents}, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error in go_to_cart: {e}")
        yield json.dumps({"status": "error", "message": "Get products from cart failed."})
        return
    
    
    

async def add_to_cart(ctx: BrowserContext, **args):
    page = await ctx.get_current_page()
    logger.info("Attempting to add product to cart")
    
    try:
        selectors = [
            '#add-to-cart-button',
            '#add-to-cart-button-ubb',
            'button[name="submit.addToCart"]',
            'input[name="submit.addToCart"]',
            '#buy-now-button'
        ]
        
        clicked = False
        for selector in selectors:
            try:
                btn = await page.query_selector(selector)
                if btn:
                    # Check if button is disabled
                    is_disabled = await btn.get_attribute('disabled')
                    style = await btn.get_attribute('style')
                    if is_disabled is not None or (style and 'not-allowed' in style):
                        # Optionally, get data-hover for more context
                        data_hover = await btn.get_attribute('data-hover')
                        msg = "The 'Add to Cart' button is disabled."
                        if data_hover:
                            msg += f" Amazon says: {data_hover.replace('<br>', ' ').replace('<b>', '').replace('</b>', '').strip()}"
                        logger.error(msg)
                        yield json.dumps({"error": msg})
                        return
                    await btn.click()
                    clicked = True
                    logger.info(f"Successfully clicked 'Add to Cart' button with selector: {selector}")
                    
                    break
            except Exception as e:
                logger.warning(f"Failed to click button with selector {selector}: {str(e)}")
                continue
                
        if not clicked:
            logger.error("No Add to Cart button found with any selector")
            yield json.dumps({"error": "Add to Cart button not found."})
            return

        # After clicking add to cart, check for warranty popup and click "No Thanks" if present
        try:
            # Wait a short time for the popup to appear
            await page.wait_for_selector('#attach-warranty-pane', state='visible', timeout=3000)
            # Click the "No Thanks" button
            no_thanks_btn = await page.query_selector('#attachSiNoCoverage input[type="submit"]')
            if no_thanks_btn:
                await no_thanks_btn.click()
                logger.info("Clicked 'No Thanks' on warranty popup.")
                # Optionally, wait for the popup to disappear
                await page.wait_for_selector('#attach-warranty-pane', state='hidden', timeout=3000)
        except Exception as e:
            logger.info("Warranty popup not shown or already handled.")

        yield json.dumps({"status": "success", "message": "Product added to cart."})
        
    except Exception as e:
        logger.error(f"Error in add_to_cart: {str(e)}")
        yield json.dumps({"status": "error", "message": f"Failed to add product to cart: {str(e)}"})
        return

async def get_order_history(ctx: BrowserContext, **args):
    page = await ctx.get_current_page()

    await page.goto(f"{AMAZON_URL}/orders")

    await asyncio.sleep(2)

    if 'amazon.com/ap/signin' in page.url:
        await sign_in(ctx)

    await page.wait_for_selector('li.order-card__list', state='visible')

    orders = []
    order_elements = await page.query_selector_all('li.order-card__list')

    for order in order_elements:
        logger.info(f"Processing order element: {order}")
    
        order_id_el = await order.query_selector('div.yohtmlc-order-id span:last-child')
        order_id = (await order_id_el.text_content()).strip() if order_id_el else None
        order_list_el = await order.query_selector_all('.a-unordered-list li .yohtmlc-product-title')

        # append order titles from the order_list_el
        order_titles = []
        for el in order_list_el:
            title = (await el.text_content()).strip()
            if title:
                order_titles.append(title)
        order_title = ', '.join(order_titles) if order_titles else None
        logger.info(f"Order ID: {order_id}, Order Title: {order_title}")
        if not order_id:
            logger.warning("Order ID not found, skipping this order.")
            return
        
        if not order_title:
            logger.warning("Order title not found, skipping this order.")
            continue
       
        date_el = await order.query_selector('.order-header span.a-size-base.a-color-secondary.aok-break-word')
        date = (await date_el.text_content()).strip() if date_el else None
     

        orders.append({
            "order_id": order_id,
            "date": date,
            "title": order_title
        })

    logger.info(f"Orders found: {(orders)}")
    yield json.dumps({"status": "success", "orders": orders}, ensure_ascii=False, indent=2)

async def cancel_order(ctx: BrowserContext, **args):
    page = await ctx.get_current_page()
    order_id = args.get("order_id")
    if not order_id:
        yield json.dumps({"error": "order_id is required"})
        return

    await page.goto(f"{AMAZON_URL}/orders")

    await asyncio.sleep(2)

    if 'amazon.com/ap/signin' in page.url:
        await sign_in(ctx)

    # add order id to search input with selector input[aria-label="Search all orders"] 
    search_input = await page.query_selector('input[aria-label="Search all orders"]')
    if search_input:
        await search_input.fill(order_id)
        await search_input.press('Enter')
    else:
        yield json.dumps({"error": "Search input not found."})
        return
    
    # Wait for the order list to load
    await asyncio.sleep(3)

    # check for selector p.hzsearch-results-summary exists, if not found, it means no orders found
    orders_found = await page.query_selector('p.hzsearch-results-summary') 

    if not orders_found:
        yield json.dumps({"error": f"No orders found for order_id: {order_id}"})
        return

    # Click on link with selector a[title="View order details"]
    await page.wait_for_selector('a[title="View order details"]', state='visible')

    order_link = await page.query_selector(f'a[title="View order details"]')

    if order_link:
        await order_link.click()

    else:
        yield json.dumps({"error": f"Order with ID {order_id} not found."})
        return

    # Wait for the order details page to load
    await asyncio.sleep(3)

   

    # Wait for the cancel button to appear
    await page.wait_for_selector('a.a-button-text:has-text("Cancel items")', state='visible')
    # If the cancel button is not found, it means the order cannot be canceled
    if not await page.query_selector('a.a-button-text:has-text("Cancel items")'):
        yield f"Order {order_id} cannot be canceled or no items selected for cancellation."
        return
    # Wait for the cancel button to be clickable

    #Click on selector a.a-button-text that has text "Cancel items"
    cancel_button = await page.query_selector('a.a-button-text:has-text("Cancel items")')
    if cancel_button:
        await cancel_button.click()
        await page.wait_for_timeout(2000)  # Wait for the cancel confirmation dialog to appear
    else:
        yield f"Cancel button not found for order {order_id}."
        return
    
     # Make sure all items are check, looking for input[name="cq.cancelItem*""] to see if checkbox is checked
    cancel_items = await page.query_selector_all('input[name^="cq.cancelItem"]')
    if not cancel_items:
        yield f"No items found to cancel for order {order_id}."
        return
    
    # check length of cancel_items, if > 1, do below

    if len(cancel_items) > 1:
        for item in cancel_items:
            await item.click()
            await asyncio.sleep(0.5)

    # click on selector input[aria-labelledby="cancelButton-announce"]
    confirm_cancel_button = await page.query_selector('input[aria-labelledby="cancelButton-announce"]')
    if confirm_cancel_button:
        await confirm_cancel_button.click()
        yield f"Order {order_id} cancellation confirmed."
        return
    else:
        yield f"Confirm cancel button not found for order {order_id}."
        return

async def request_refund(ctx: BrowserContext, **args):
    page = await ctx.get_current_page()
    order_id = args.get("order_id")
    
    gen_id = IncrementID()

    task = 'Strictly follow the instructions below:\n'
    task += f'{gen_id()}. Go to Your Orders to display your recent orders. To return a gift, go to Return a Gift.\n'
    task += f'{gen_id()}. Find and choose the order with ID {order_id} and select Return or Replace Items. If not found "Return or Replace" button, stop and tell user order not found\n'
    task += f'{gen_id()}. Select the item that you want to return. Then select an option from the Reason for return (choose Other) menu.\n'
    task += f'{gen_id()}. Choose how to process your return. If applicable, select to issue a refund or replacement. For items sold from an Amazon seller, Submit a return request. The Amazon seller reviews return requests before issuing a refund or replacement. For more information, go to Returns to Third-Party Sellers. If you don\'t receive a response within two business days, you can request an A-to-z Guarantee Refund.\n'
    task += f'{gen_id()}. Select your preferred return method. Choose method to refund to user card\n'
    task += f'{gen_id()}. Click confirmation button.\n'

    try:
        msg = await browse(task, ctx, max_steps=10)
        yield msg
    except Exception as e:
        logger.error(f"Error during refund process: {e}")
        yield json.dumps({"error": f"Failed to request refund for order {order_id}: {str(e)}"})
        return
    yield json.dumps({"status": "success", "message": f"Refund request for order {order_id} has been initiated."})

async def adjust_cart(ctx: BrowserContext, **args):
    page = await ctx.get_current_page()
    selector = args.get("selector")
    if not selector:
        yield json.dumps({"error": "Both 'selector' are required."})
        return

    if normalize_url(page.url) != normalize_url(f"{AMAZON_URL}/cart"):
        await page.goto(f"{AMAZON_URL}/cart")
    
    try:
        await page.wait_for_load_state('domcontentloaded')
        element = await page.query_selector(selector)
        if not element:
            yield json.dumps({"error": f"Element with selector '{selector}' not found on page."})
            return
        await element.click()
        await asyncio.sleep(1)

        # Find the parent cart item element
        cart_item = await element.evaluate_handle('el => el.closest(".sc-list-item")')
        # Product name
        product_name = None
        if cart_item:
            title_el = await cart_item.query_selector('.sc-product-title')
            if title_el:
                product_name = (await title_el.text_content()).strip()
        # Quantity
        quantity = 1
        if cart_item:
            quantity_el = await cart_item.query_selector('div[role="spinbutton"]')
            if quantity_el:
                try:
                    quantity_val = await quantity_el.get_attribute('aria-valuenow')
                    if quantity_val:
                        quantity = int(quantity_val)
                except Exception:
                    pass
            else:
                
                quantity_span = await cart_item.query_selector('span[data-a-selector="value"]')
                if quantity_span:
                    try:
                        quantity_val = await quantity_span.text_content()
                        if quantity_val:
                            quantity = int(quantity_val)
                    except Exception:
                        pass
        yield json.dumps({"status": "success", "message": f"Clicked element '{selector}' on page.", "product_name": product_name, "quantity": quantity})
    except Exception as e:
        yield json.dumps({"status": "error", "message": f"Failed to click element '{selector}': {str(e)}"})
        return
