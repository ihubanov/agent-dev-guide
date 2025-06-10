functions = [
        {
            "type": "function",
            "function": {
                "name": "search_products",
                "description": "Search products with the specified criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query to search for. For example, 'laptop'"
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False
                },
                "strict": False
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_product_detail",
                "description": "Get product detail from the link.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "link": {
                            "type": "string",
                            "description": "The link of the product to get detail for."
                        }
                    },
                    "required": ["link"],
                    "additionalProperties": False
                },
                "strict": False
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_to_cart",
                "description": "Click 'Add to Cart' button",
                "parameters": None,
                "strict": False
            }
        },
        {
            "type": "function",
            "function": {   
                "name": "go_to_cart",
                "description": "Open the shopping cart page",
                "parameters": None,
                "strict": False
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_out",
                "description": "Complete the checkout process until order is placed.",
                "parameters": None,
                "strict": False
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_order_history",
                "description": "Get the order history of the user.",
                "parameters": None,
                "strict": False
            }
        },
        {
            "type": "function",
            "function": {
                "name": "cancel_order",
                "description": "Cancel an order by its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The ID of the order to cancel."
                        }
                    },
                    "required": ["order_id"],
                    "additionalProperties": False
                },
                "strict": False
            }
        },
        {
            "type": "function",
            "function": {
                "name": "request_refund",
                "description": "Request a refund for an order by its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The ID of the order to request a refund for."
                        }
                    },
                    "required": ["order_id"],
                    "additionalProperties": False
                },
                "strict": False
            }
        },
        {
            "type": "function",
            "function": {
                "name": "adjust_cart",
                "description": "Adjust the quantity of a product in the cart.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "The CSS selector of the element to click. For example, increment_quantity_selector, decrement_quantity_selector, or remove_button_selector."
                        }
                    },
                    "required": ["selector"],
                    "additionalProperties": False
                },
                "strict": False
            }
        }
]

def get_functions():
    return functions
