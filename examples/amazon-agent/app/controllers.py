import logging

from browser_use import Controller

logger = logging.getLogger(__name__)

built_in_actions = [
    'done',
    'search_google',
    'go_to_url',
    'go_back',
    'wait',
    'click_element_by_index',
    'input_text',
    'save_pdf',
    'switch_tab',
    'open_tab',
    'close_tab',
    'extract_content',
    'scroll_down',
    'scroll_up',
    'send_keys',
    'scroll_to_text',
    'get_dropdown_options',
    'select_dropdown_option',
    'drag_drop',
    'get_sheet_contents',
    'select_cell_or_range',
    'get_range_contents',
    'clear_selected_range',
    'input_selected_cell_text',
    'update_range_contents' 
]

exclude = [
    a
    for a in built_in_actions
    if a not in [
        'done',
        'go_to_url',
        'go_back',
        'click_element_by_index',
        'input_text',
        'extract_content',
        'scroll_down',
        'scroll_up',
        'send_keys',
        'get_dropdown_options',
        'select_dropdown_option',
        'update_range_contents' 
    ]
]

_controller = Controller(
    exclude_actions=exclude
)

def get_controller():
    global _controller
    return _controller
