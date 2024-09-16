#!/bin/bash
curl -X POST \
  -d '{"yandexPassportOauthToken":""}' \
  https://iam.api.cloud.yandex.net/iam/v1/tokens
