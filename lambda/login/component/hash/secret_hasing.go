package hash

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"errors"
	"strings"
)

func CreateSecretHash(clientSecret, user, clientPoolID string) string {
	mac := hmac.New(sha256.New, []byte(clientSecret))
	mac.Write([]byte(user + clientPoolID))
	return base64.StdEncoding.EncodeToString(mac.Sum(nil))
}

func ExtractTokenFromHeader(header string) (string, error) {
	parts := strings.Split(header, " ")
	if parts[0] != "Bearer" || len(parts) < 2 || strings.TrimSpace(parts[1]) == "" {
		return "", errors.New("wrong authen header")
	}
	return parts[1], nil
}
