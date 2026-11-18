---
title: SSL 검사 프록시 환경에서 AWS CLI 인증서 오류
type: article
status: draft
confidential: public
tags: [aws, aws-cli, sso, tls, proxy]
---

# SSL 검사 프록시 환경에서 AWS CLI 인증서 오류

> Sources: Claude Code 세션 요약, 2026-11-17
> Raw: [세션 요약 2026-11-17](../../raw/sessions/2026-11-17.md)
> Updated: 2026-11-18

## Overview

회사 PC처럼 HTTPS를 중간에서 검사하는 SSL 프록시가 있는 환경에서 `aws sso login` 이
`unable to get local issuer certificate` 로 실패한다. AWS CLI v2는 **자체 Python과 CA 목록을 번들로
갖고 있어** OS 키체인에 등록된 프록시 루트 CA를 신뢰하지 않기 때문이다.

## 원인

- AWS OIDC 엔드포인트에 접속하면 AWS 원래 인증서가 아니라 프록시가 재발급한 인증서가 돌아온다
- AWS CLI v2는 따로 알려주지 않으면 그 루트 CA를 모른다

## 해결

`AWS_CA_BUNDLE` 환경변수로 프록시 루트 CA가 포함된 번들 파일을 지정한다.

당시 사례에서는 셸 설정 파일에 이미 `AWS_CA_BUNDLE` 이 있었는데, **로그인을 시도한 터미널 세션에
환경변수가 잡혀 있지 않아서** 실패했다. 설정이 있는데도 실패하면 현재 셸에서 변수가 실제로
export 됐는지부터 본다.

## See Also

- 같은 날 클러스터 확인이 SSO 토큰 만료로 막힌 일이 있었다. SSO 세션 만료 → 재로그인 → 이 오류 순서로 이어지기 쉽다.
