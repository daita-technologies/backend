package usermodel

type EventID struct {
	ID   string `json:"event_ID"`
	Type string `json:"type"`
}

const TBL_EventID = "eventUser"
