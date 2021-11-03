import re
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import Required, Email, Length, EqualTo, ValidationError


# Character check for First name and Last name fields.
def character_check(form, field):
    excluded_chars = "?!'^+%&/()=}][{$#@<>"
    chars_present = ""
    for char in field.data:
        if char in excluded_chars:
            if char not in chars_present:
                chars_present += char
    if chars_present != "":
        if len(chars_present) == 1:
            raise ValidationError(
                f"Character {chars_present} is not allowed.")
        else:
            raise ValidationError(
                f"Characters {chars_present} are not allowed.")


class RegisterForm(FlaskForm):
    email = StringField(validators=[Required(), Email()])
    firstname = StringField(validators=[Required(), character_check])
    lastname = StringField(validators=[Required(), character_check])
    phone = StringField(validators=[Required()])
    password = PasswordField(validators=[Required(), Length(min=6, max=12, message='Password must be between 6 and '
                                                                                   '12 characters in length.')])
    confirm_password = PasswordField(validators=[Required(), EqualTo('password', message='Both password fields '
                                                                                         'must be equal!')])
    pin_key = StringField(validators=[Required(), Length(min=32, max=32, message='PIN key must be 32 '
                                                                                 'characters long.')])
    submit = SubmitField()

    # Password validation check to see if it contains characters needed.
    def validate_password(self, password):
        p = re.compile(r'(?=.*\d)(?=.*[A-Z])(?=.*[a-z])(?=.*\W)')
        if not p.match(self.password.data):
            raise ValidationError("Password must contain at least 1 digit, 1 lowercase, 1 uppercase and "
                                  "1 special character.")

    # Phone validation to check for correct formatting
    def validate_phone(self, phone):
        p = re.compile(r'\d{4}-\d{3}-\d{4}')
        if not p.match(self.phone.data):
            raise ValidationError("Please use the following phone format (including the dashes): XXXX-XXX-XXXX.")


class LoginForm(FlaskForm):
    username = StringField(validators=[Required(), Email()])
    password = PasswordField(validators=[Required()])
    submit = SubmitField()
