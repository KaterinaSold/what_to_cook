from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from app.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Повторите пароль',
                             validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Это имя пользователя уже занято.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Этот email уже зарегистрирован.')

class IngredientForm(FlaskForm):
    name = StringField('Название ингредиента', validators=[DataRequired(), Length(max=100)])
    calories = FloatField('Калории (на 100г)', validators=[DataRequired()])
    proteins = FloatField('Белки (г на 100г)', validators=[DataRequired()])
    fats = FloatField('Жиры (г на 100г)', validators=[DataRequired()])
    carbs = FloatField('Углеводы (г на 100г)', validators=[DataRequired()])
    is_public = BooleanField('Сделать общедоступным')
    submit = SubmitField('Сохранить')

class RecipeForm(FlaskForm):
    name = StringField('Название рецепта', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Описание (опционально)', validators=[Optional(), Length(max=500)])
    instructions = TextAreaField('Инструкции приготовления', validators=[DataRequired()])
    image_url = StringField('URL изображения (опционально)', validators=[Optional(), Length(max=500)])
    is_public = BooleanField('Сделать общедоступным')
    submit = SubmitField('Сохранить')

class RecipeIngredientForm(FlaskForm):
    """Форма для добавления ингредиента в рецепт"""
    existing_ingredient = SelectField('Выберите ингредиент', coerce=int, validators=[Optional()])
    new_ingredient_name = StringField('Или создайте новый', validators=[Optional()])
    calories = FloatField('Калории (на 100г)', validators=[Optional()])
    proteins = FloatField('Белки (г на 100г)', validators=[Optional()])
    fats = FloatField('Жиры (г на 100г)', validators=[Optional()])
    carbs = FloatField('Углеводы (г на 100г)', validators=[Optional()])
    amount = IntegerField('Количество (г)', validators=[DataRequired()])

class CalculationForm(FlaskForm):
    target_calories = FloatField('Целевые калории', validators=[DataRequired()])
    target_proteins = FloatField('Целевые белки (г)', validators=[DataRequired()])
    target_fats = FloatField('Целевые жиры (г)', validators=[DataRequired()])
    target_carbs = FloatField('Целевые углеводы (г)', validators=[DataRequired()])
    submit = SubmitField('Рассчитать')