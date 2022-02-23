package common

import (
	"errors"
)

const (
	MessageUnmarshalInputJson                    = "Unmarshal unexpected end of JSON input"
	MessageAuthenFailed                          = "Authentication failed"
	MessageLoginFailed                           = "Username or password is incorrect"
	MessageSignUpFailed                          = "Sign up failed"
	MessageSignInSuccessfully                    = "Login successful"
	MessageMissingAuthorizationHeader            = "Missing authorization header"
	MessageConfirmWrongCodeSignUP                = "A wrong confirmation code has been entered. If you have requested a new confirmation code, use only the latest code."
	MessageUserVerifyConfirmCode                 = "User need to verify confirmation code"
	MessageSignUPEmailInvalid                    = "This email address is already being used"
	MessageSignUpUsernameInvalid                 = "This username is already being used"
	MessageSignUpInvalid                         = "Both username and email are already being used"
	MessageResendEmailConfirmCodeSuccessfully    = "Email successfully sent"
	MessageResendEmailConfirmCodeFailed          = "Email delivery failed"
	MessageInvalidPassword                       = "Password rules are at least 8 characters, at least 1 lower case letter, at least 1 upper case letter, at least 1 number, and at least 1 special character."
	MessageVerifyConfirmcodeWrong                = "Invalid confirmation code provided"
	MessageTheValueNotExistInDatabase            = "The value does not exist in the database"
	MessageRefreshTokenError                     = "Refreshing the token failed"
	MessageRefreshTokenSuccessfully              = "Refreshing the token was successful"
	MessageForgotPasswordFailed                  = "Forgot password failed"
	MessageForgotPasswordUsernotExist            = "Username does not exist"
	MessageForgotPasswordSuccessfully            = "Email for password recovery successfully sent"
	MessageForgotPasswordConfirmcodeSuccessfully = "Confirmation code for password recovery was successful"
	MessageForgotPasswordConfirmcodeFailed       = "Confirmation code for password recovery failed"
	MessageCannotRegisterMoreUser                = "We cannot register more users currently"
	MessageTokenInvalid                          = "Token is invalid"
	MessageGetTemapleMailSuccessFully            = "Template for friend invitation received successfully"
	MessageErrorDeleteUserSignUp                 = "Error deleting user"
	MessageCaptchaFailed                         = "Captcha token verification failed"
)

var (
	ErrMessageErrorDeleteUserSignUp    = errors.New(MessageErrorDeleteUserSignUp)
	ErrCannotRegisterMoreUser          = errors.New(MessageCannotRegisterMoreUser)
	ErrForgotPasswordConfirmcodeFailed = errors.New(MessageForgotPasswordConfirmcodeFailed)
	ErrForgotPasswordUserNotExist      = errors.New(MessageForgotPasswordUsernotExist)
	ErrForgotPasswordFailed            = errors.New(MessageForgotPasswordFailed)
	ErrUnmarshalInputJson              = errors.New(MessageUnmarshalInputJson)
	ErrAuthenFailed                    = errors.New(MessageAuthenFailed)
	ErrSignedUpFailed                  = errors.New(MessageSignUpFailed)
	ErrInit                            = errors.New("")
	ErrLoginFailed                     = errors.New(MessageLoginFailed)
	ErrWrongConfirmCodeSignUp          = errors.New(MessageConfirmWrongCodeSignUP)
	ErrUserVerifyConfirmCode           = errors.New(MessageUserVerifyConfirmCode)
	ErrUserSignUpInvalid               = errors.New(MessageSignUpInvalid)
	ErrSendEmailFailed                 = errors.New(MessageResendEmailConfirmCodeFailed)
	ErrInvalidPassword                 = errors.New(MessageInvalidPassword)
	ErrInvalidConfirmCode              = errors.New(MessageVerifyConfirmcodeWrong)
	ErrValueNotExist                   = errors.New(MessageTheValueNotExistInDatabase)
	ErrRefreshToken                    = errors.New(MessageRefreshTokenError)
	ErrTokenInvalid                    = errors.New(MessageTokenInvalid)
	ErrCaptchaFailed                   = errors.New(MessageCaptchaFailed)
)

var ErrCogintoResponse = []string{"minimum field size of 6", "User is not confirmed", "Invalid verification code provided", "User does not exist"}
var ErrorMessageCoginto = []error{ErrInvalidPassword, ErrUserVerifyConfirmCode, ErrInvalidConfirmCode, ErrForgotPasswordUserNotExist}
