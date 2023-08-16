from apps import db


class Recipes(db.Model):

    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String)
    image_url = db.Column(db.Text)
    description = db.Column(db.Text)
    instruction = db.Column(db.Text)
    ingredient = db.Column(db.Text)
    minutes = db.Column(db.SmallInteger)
    created_at = db.Column(db.TIMESTAMP)

    user = db.relationship('Users')


class RecipeLikes(db.Model):

    __tablename__ = 'recipe_likes'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    user = db.relationship('Users')
    recipe = db.relationship('Recipes')


class Comments(db.Model):

    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment_text = db.Column(db.String)
    commented_at = db.Column(db.TIMESTAMP)

    user = db.relationship('Users')
    recipe = db.relationship('Recipes')


class RecipeCategories(db.Model):

    __tablename__ = 'recipe_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)


class RecipeCategoryMapping(db.Model):
    __tablename__ = 'recipe_category_mapping'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('recipe_categories.id'))

    recipe = db.relationship('Recipes')
    category = db.relationship(
        'RecipeCategories')
