from flask import jsonify, request, render_template, url_for, redirect
from tempfile import NamedTemporaryFile
import os

from apps import db
from apps.authentication.middleware import token_required
from apps.recipe import blueprint
from apps.authentication.models import Users
from apps.config import Config

from datetime import datetime

from .models import Recipes, RecipeLikes, Comments, RecipeCategories, RecipeCategoryMapping
from .forms import CommentForm, RecipeForm


# RECIPES
# Get all recipes
@blueprint.route('/recipes', methods=['GET'])
@token_required
def index(request):
    recipes = Recipes.query.all()
    recipe_list = []
    for recipe in recipes:
        # Count likes and comments for the recipe
        like_count = RecipeLikes.query.filter_by(recipe_id=recipe.id).count()

        comment_count = Comments.query.filter_by(recipe_id=recipe.id).count()

        recipe_list.append({
            'id': recipe.id,
            'user_id': recipe.user_id,
            'title': recipe.title,
            'image_url': recipe.image_url,
            'description': recipe.description,
            'like_count': like_count,
            'comment_count': comment_count
        })

    return render_template('recipe/index.html', recipes=recipe_list)


# Create a new recipe
@blueprint.route('/recipes/create', methods=['GET', 'POST'])
@token_required
def create_recipe(current_user):
    recipe_form = RecipeForm(request.form)

    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            instruction = request.form.get('instruction')
            minutes = request.form.get('minutes')
            category = request.form.get('category')
            ingredient = request.form.getlist('ingredient[]')
            image = request.files.get('image')

            image_url = Config.SUPABASE_STORAGE_URL

            if image:
                # Save the image to a temporary file
                with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    image.save(temp_file)

                # Upload the temporary file to Supabase Storage
                temp_file_path = temp_file.name
                # Adjust destination path as needed
                destination = f"admin/{image.filename}"
                image_url += f'/{image.filename}'

            new_recipe = Recipes(user_id=current_user.id,
                                 title=title,
                                 description=description,
                                 image_url=image_url,
                                 ingredient=ingredient,
                                 instruction=instruction,
                                 minutes=minutes,
                                 created_at=datetime.now())

            db.session.add(new_recipe)
            db.session.flush()

            recipe_category = RecipeCategories.query.filter(
                RecipeCategories.name == category).first()
            recipe_id = new_recipe.id
            recipe_category_id = recipe_category.id

            if not recipe_category:
                return jsonify({"message": "Category not found", "error": True}), 404

            mapping = RecipeCategoryMapping(
                recipe_id=recipe_id, category_id=recipe_category_id)

            with open(temp_file_path, 'rb') as f:
                Config.supabase.storage.from_(
                    'recipes').upload(destination, f)

            # Delete the temporary file
            os.remove(temp_file_path)

            db.session.add(mapping)
            db.session.commit()

            return redirect(url_for('recipe_blueprint.index'))

        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Something went wrong", "error": str(e)}), 500
    else:
        return render_template('recipe/index.html', form=recipe_form)


# Get a single recipe
@blueprint.route('/recipes/<int:id>', methods=['GET'])
def get_recipe(id):
    recipe = Recipes.query.get(id)
    if recipe is None:
        return jsonify({'error': 'Recipe not found'}), 404
    like_count = RecipeLikes.query.filter_by(recipe_id=recipe.id).count()

    # Get the comments
    comments = Comments.query.filter_by(recipe_id=recipe.id).all()
    # Extract comment_text and user_id from each comment
    comment_info = [{'user_id': comment.user_id,
                     'comment_text': comment.comment_text} for comment in comments]

    # Retrieve usernames and image URLs for each user_id
    user_ids = [comment['user_id'] for comment in comment_info]

    # Query the Users table to get usernames and image URLs
    users = Users.query.filter(Users.id.in_(user_ids)).all()

    # Create a dictionary to map user_id to user information
    user_info_map = {user.id: {'username': user.username,
                               'image_url': user.image_url} for user in users}

    # Append usernames and image URLs to comment_info
    for comment in comment_info:
        user_info = user_info_map.get(comment['user_id'])
        if user_info:
            comment['username'] = user_info['username']
            comment['image_url'] = user_info['image_url']

    ingredient = recipe.ingredient
    ingredient = ingredient.strip('{}')
    ingredient_list = [item.strip('"') for item in ingredient.split(',')]

    recipe = {
        'id': recipe.id,
        'user_id': recipe.user_id,
        'title': recipe.title,
        'image_url': recipe.image_url,
        'description': recipe.description,
        'like_count': like_count,
        'comments': comment_info,
        'instructions': recipe.instruction,
        'ingredients': ingredient_list
    }
    return render_template('recipe/recipe.html', recipe=recipe)


# Give like and comment
@blueprint.route('/recipes/<int:recipe_id>/like', methods=['POST'])
@token_required
def like_recipe(current_user, recipe_id):
    try:
        recipe = Recipes.query.get(recipe_id)
        if not recipe:
            return jsonify({"message": "Recipe not found", "error": True}), 404

        # Check if the user has already liked the recipe
        if RecipeLikes.query.filter_by(user_id=current_user.id, recipe_id=recipe.id).first():
            return jsonify({"message": "You've already liked this recipe", "error": True}), 400

        # Create a new RecipeLike entry
        like = RecipeLikes(user_id=current_user.id, recipe_id=recipe.id)
        db.session.add(like)
        db.session.commit()

        return jsonify({"message": "Recipe liked successfully", "error": False}), 201

    except Exception as e:
        return jsonify({"message": "Something went wrong", "error": str(e)}), 500


@blueprint.route('/recipes/<int:recipe_id>/comments', methods=['GET', 'POST'])
@token_required
def comment_on_recipe(current_user, recipe_id):
    comment_form = CommentForm(request.form)

    recipe = Recipes.query.get(recipe_id)
    if not recipe:
        return jsonify({"message": "Recipe not found", "error": True}), 404

    if request.method == 'POST':
        try:
            comment_text = request.form['comment_text']

            # Create a new Comment entry
            comment = Comments(
                user_id=current_user.id,
                recipe_id=recipe.id,
                comment_text=comment_text,
                commented_at=datetime.now()
            )
            db.session.add(comment)
            db.session.commit()

            return redirect(url_for('recipe_blueprint.get_recipe', id=recipe_id))

        except Exception as e:
            return jsonify({"message": "Something went wrong", "error": str(e)}), 500
    else:
        # Get the comments
        comments = Comments.query.filter_by(recipe_id=recipe.id).all()
        # Extract comment_text and user_id from each comment
        comment_info = [{
            'user_id': comment.user_id,
            'username': comment.user_id.username,
            'user_image': comment.user_id.image_url,
            'comment_text': comment.comment_text
        } for comment in comments]
        return render_template('recipe/comment.html', comments=comment_info, form=comment_form)


# Categories
@blueprint.route('/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'GET':
        categories = RecipeCategories.query.all()
        category_data = [{'id': category.id, 'name': category.name}
                         for category in categories]
        return jsonify(category_data)

    if request.method == 'POST':
        data = request.json
        name = data.get('name')

        if not name:
            return jsonify({"message": "Name is required", "error": True}), 400

        new_category = RecipeCategories(name=name)
        db.session.add(new_category)
        db.session.commit()

        return jsonify({"message": "Category created successfully", "error": False}), 201


@blueprint.route('/recipes/<int:recipe_id>/categories', methods=['GET', 'POST', 'DELETE'])
def recipe_categories(recipe_id):
    recipe = Recipes.query.get(recipe_id)

    if not recipe:
        return jsonify({"message": "Recipe not found", "error": True}), 404

    if request.method == 'GET':
        categories_mapping = RecipeCategoryMapping.query.filter_by(
            recipe_id=recipe_id).all()
        category_data = [{'id': category.category_id, 'name': category.category.name}
                         for category in categories_mapping]
        return jsonify(category_data)

    if request.method == 'POST':
        data = request.json
        category_id = data.get('category_id')

        if not category_id:
            return jsonify({"message": "Category ID is required", "error": True}), 400

        category = RecipeCategories.query.get(category_id)
        if not category:
            return jsonify({"message": "Category not found", "error": True}), 404

        # Check if the mapping already exists
        if RecipeCategoryMapping.query.filter_by(recipe_id=recipe_id, category_id=category_id).first():
            return jsonify({"message": "Mapping already exists", "error": True}), 400

        mapping = RecipeCategoryMapping(
            recipe_id=recipe_id, category_id=category_id)
        db.session.add(mapping)
        db.session.commit()

        return jsonify({"message": "Mapping created successfully", "error": False}), 201

    if request.method == 'DELETE':
        data = request.json
        category_id = data.get('category_id')

        if not category_id:
            return jsonify({"message": "Category ID is required", "error": True}), 400

        mapping = RecipeCategoryMapping.query.filter_by(
            recipe_id=recipe_id, category_id=category_id).first()

        if not mapping:
            return jsonify({"message": "Mapping not found", "error": True}), 404

        db.session.delete(mapping)
        db.session.commit()

        return jsonify({"message": "Mapping deleted successfully", "error": False}), 200


@blueprint.route('/search', methods=['GET'])
def search_recipes():
    search_title = request.args.get('search_title', '').lower()

    recipes = Recipes.query.filter(
        Recipes.title.ilike(f"%{search_title}%")).all()
    filtered_recipes = []
    for recipe in recipes:
        # Count likes and comments for the recipe
        like_count = RecipeLikes.query.filter_by(recipe_id=recipe.id).count()

        comment_count = Comments.query.filter_by(recipe_id=recipe.id).count()

        filtered_recipes.append({
            'id': recipe.id,
            'user_id': recipe.user_id,
            'title': recipe.title,
            'image_url': recipe.image_url,
            'description': recipe.description,
            'like_count': like_count,
            'comment_count': comment_count
        })

    return render_template('recipe/index.html', recipes=filtered_recipes)


@blueprint.route('/recipes/<category_name>', methods=['GET'])
def filter_by_category(category_name):
    # Get category by name
    category = RecipeCategories.query.filter_by(name=category_name).first()
    if not category:
        return "Category not found", 404

    # Get recipes associated with the given category
    recipe_ids = [mapping.recipe_id for mapping in RecipeCategoryMapping.query.filter_by(
        category_id=category.id).all()]

    recipes = Recipes.query.filter(Recipes.id.in_(recipe_ids))

    filtered_recipes = []
    for recipe in recipes:
        # Count likes and comments for the recipe
        like_count = RecipeLikes.query.filter_by(recipe_id=recipe.id).count()
        comment_count = Comments.query.filter_by(recipe_id=recipe.id).count()

        filtered_recipes.append({
            'id': recipe.id,
            'user_id': recipe.user_id,
            'title': recipe.title,
            'image_url': recipe.image_url,
            'description': recipe.description,
            'like_count': like_count,
            'comment_count': comment_count
        })

    return render_template('recipe/index.html', recipes=filtered_recipes)
