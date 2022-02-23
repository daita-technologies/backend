package usermodel

const TBL_consts = "consts"

type Consts struct {
	Code       string `json:"code"`
	Type       string `json:"type"`
	Descripton string `json:"descripton"`
	Num_value  int    `json:"num_value"`
}
