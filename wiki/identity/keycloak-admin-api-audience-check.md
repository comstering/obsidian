---
title: Keycloak 26.8.2 Admin API audience 검사와 Terraform provider 인증 실패
type: article
status: draft
confidential: public
tags: [keycloak, terraform, upgrade, breaking-change]
---

# Keycloak 26.8.2 Admin API audience 검사와 Terraform provider 인증 실패

> Sources: Claude Code 세션 요약, 2026-11-12
> Raw: [세션 요약 2026-11-12](../../raw/sessions/2026-11-12.md)
> Updated: 2026-11-18

## Overview

Keycloak을 26.8.2로 올린 뒤 Terraform keycloak provider가 인증 단계에서 실패했다.
세션 기록에 따르면 원인은 26.8.2에서 들어온 breaking change로, **Admin REST API가 Bearer 토큰의
audience를 검사**하기 시작했기 때문이다. 26.8.0까지는 문제가 없었다.

## 원인 (세션 기록 기준)

- 26.8.2 공식 업그레이드 가이드의 Admin REST API audience 검사 항목에 해당하는 변경
- provider가 client_credentials로 받은 토큰에 Admin API용 `aud` 가 없으면 거부된다
- 26.8.1의 breaking change(SMTP STARTTLS 필수, X.509 key usage/EKU 검증 강화, CRL 경로·크기 제한,
  backchannel logout 토큰 서명 검증 등)는 provider의 client_credentials 로그인과 무관하다고 정리했다

## 대응 방향

provider가 쓰는 client의 토큰에 Admin API audience가 들어가도록 설정해야 한다
(예: audience mapper 추가). 업그레이드 전 해당 버전의 upgrading guide에서 Admin API 관련 항목을 먼저 확인한다.

> **Status: 근거 미비**
> 세션 요약에만 근거한다. 실제로 audience 설정을 적용해 provider 인증이 복구됐는지는 기록에 없다.
> 공식 upgrading guide 원문을 `raw/` 에 편입하면 verified로 올릴 수 있다.

## See Also

- [Keycloak IdP 첫 로그인 시 기존 사용자 자동 연결](keycloak-first-broker-login-auto-link.md)
