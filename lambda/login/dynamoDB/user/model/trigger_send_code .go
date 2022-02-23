package usermodel

const TBL_TRIGGER_SEND_CODE = "Trigger_send_code"

type SendCode struct {
	User string `json:"user"`
	Code string `json:"code"`
}
