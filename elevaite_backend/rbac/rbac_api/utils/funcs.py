from sqlalchemy import func

def snake_to_camel(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def construct_jsonb_path_expression(JSONB_obj, permission_path: list[str], action_value: str):
    jsonb_path_expression = func.jsonb_extract_path_text(JSONB_obj, *permission_path) == action_value
    return jsonb_path_expression
