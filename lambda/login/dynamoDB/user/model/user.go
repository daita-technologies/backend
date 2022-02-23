package usermodel

type UserSignUP struct {
	UserName string `json:"username"`
	Password string `json:"password"`
	Email    string `json:"email"`
	Captcha  string `json:"captcha"`
}

type UserSignUpConfirm struct {
	Username    string `json:"username"`
	ConfirmCode string `json:"confirm_code"`
}

type UserLogin struct {
	UserName string `json:"username"`
	Password string `json:"password"`
	Captcha  string `json:"captcha"`
}
type User struct {
	ID         string `json:"ID"`
	UserName   string `json:"username"`
	IdentityID string `json:"identity_id"`
	Status     string `json:"status"`
	Role       string `json:"role"`
	CreateAt   string `json:"create_at"`
	UpdateAt   string `json:"update_at"`
	KMSKeyID   string `json:"kms_key_id"`
}

type UserUpdateVerify struct {
	ID         string `json:"ID"`
	IdentityID string `json:"identity_id"`
	Status     string `json:"status"`
	KMSKeyID   string `json:"kms_key_id"`
}
type UserAuthResponse struct {
	Token                    string `json:"token"`
	CredentialTokenExpiresIn int64  `json:"credential_token_expires_in"`
	TokenExpiresIn           int64  `json:"token_expires_in"`
	IDToken                  string `json:"id_token"`
	AccessKey                string `json:"access_key"`
	IdentityID               string `json:"identity_id"`
	SecretKey                string `json:"secret_key"`
	SessionKey               string `json:"session_key"`
	ResfreshToken            string `json:"resfresh_token"`
}
type UserRefreshTokenResponse struct {
	Token                    string `json:"token"`
	CredentialTokenExpiresIn int64  `json:"credential_token_expires_in"`
	TokenExpiresIn           int64  `json:"token_expires_in"`
	IDToken                  string `json:"id_token"`
	AccessKey                string `json:"access_key"`
	IdentityID               string `json:"identity_id"`
	SecretKey                string `json:"secret_key"`
	SessionKey               string `json:"session_key"`
}
type UserResendEmail struct {
	UserName string `json:"username"`
}

type UserForgotPassword struct {
	UserName string `json:"username"`
	Captcha  string `json:"captcha"`
}

type UserRefreshToken struct {
	UserName     string `json:"username"`
	RefreshToken string `json:"refresh_token"`
}

type ResponseVerfifyCatpcha struct {
	Success  bool   `json:"success"`
	Hostname string `json:"hostname"`
}

type UserSendConfirmForgotPassword struct {
	UserName    string `json:"username"`
	Password    string `json:"password"`
	ConfirmCode string `json:"confirm_code"`
}

type UserLoginSocialResponse struct {
	ID_Token      string `json:"id_token"`
	Token         string `json:"access_token"`
	ResfreshToken string `json:"refresh_token"`
}

const TBL_USER = "User"
