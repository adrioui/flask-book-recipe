# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, FieldList, FileField
from wtforms.validators import DataRequired


# Recipe
class RecipeForm(FlaskForm):
    title = StringField('Title',
                        id='title',
                        validators=[DataRequired()])
    description = StringField('Description',
                              id='description',
                              validators=[DataRequired()])
    image = FileField('image', validators=[DataRequired()])
    category = StringField('Category',
                           id='category',
                           validators=[DataRequired()])
    ingredients = FieldList(StringField(
        'Ingredient', validators=[DataRequired()]), min_entries=1)
    instruction = StringField('Instruction',
                              id='instruction',
                              validators=[DataRequired()])


class CommentForm(FlaskForm):
    comment = StringField('Comment',
                          id='comment',
                          validators=[DataRequired()])
