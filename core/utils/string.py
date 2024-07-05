

def to_snake_case(snake_case_string:str):
    words = snake_case_string.split('_')
    return ' '.join(word.capitalize() for word in words)
