.PHONY: build clean deploy

build:
	gofmt -s -w .
	dep ensure -v
	env GOARCH=amd64 GOOS=linux go build  -mod=readonly  -ldflags="-s -w" -o bin/login ./deploy/login.go
	env GOARCH=amd64 GOOS=linux go build  -mod=readonly  -ldflags="-s -w" -o bin/resend_confirmcode ./deploy/resend_confirmcode.go
	env GOARCH=amd64 GOOS=linux go build  -mod=readonly  -ldflags="-s -w" -o bin/sign_out ./deploy/sign_out.go
	env GOARCH=amd64 GOOS=linux go build  -mod=readonly  -ldflags="-s -w" -o bin/sign_up ./deploy/sign_up.go
	env GOARCH=amd64 GOOS=linux go build  -mod=readonly  -ldflags="-s -w" -o bin/test ./deploy/test.go
	env GOARCH=amd64 GOOS=linux go build  -mod=readonly  -ldflags="-s -w" -o bin/auth_confirm ./deploy/auth_confirm.go
	env GOARCH=amd64 GOOS=linux go build  -mod=readonly  -ldflags="-s -w" -o bin/confirm_code_forgot_password ./deploy/confirm_code_forgot_password.go
	env GOARCH=amd64 GOOS=linux go build  -mod=readonly  -ldflags="-s -w" -o bin/forgot_password ./deploy/forgot_password.go
	env GOARCH=amd64 GOOS=linux go build  -mod=readonly  -ldflags="-s -w" -o bin/login_refresh_token ./deploy/login_refresh_token.go
	env GOARCH=amd64 GOOS=linux go build  -mod=readonly  -ldflags="-s -w" -o bin/template_email ./deploy/template_email.go
	env GOARCH=amd64 GOOS=linux go build  -mod=readonly  -ldflags="-s -w" -o bin/login_social ./deploy/login_social.go

clean:
	rm -rf ./bin ./vendor Gopkg.lock

deploy: clean build
	sls deploy --verbose
