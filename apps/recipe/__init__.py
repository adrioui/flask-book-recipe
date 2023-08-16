from flask import Blueprint

blueprint = Blueprint(
    'recipe_blueprint',
    __name__,
    url_prefix=''
)
