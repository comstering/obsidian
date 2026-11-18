---
title: Keycloak IdP 첫 로그인 시 기존 사용자 자동 연결
type: article
status: draft
confidential: public
tags: [keycloak, okta, idp, oidc, terraform]
---

# Keycloak IdP 첫 로그인 시 기존 사용자 자동 연결

> Sources: Claude Code 세션 요약, 2026-11-13
> Raw: [세션 요약 2026-11-13](../../raw/sessions/2026-11-13.md)
> Updated: 2026-11-18

## Overview

Keycloak에 외부 IdP(Okta OIDC)를 붙였을 때, 같은 username·email의 로컬 유저가 이미 있으면
"already exists" 화면이 뜨고 연결되지 않는다. 기본 `first broker login` flow의 동작이다.
세션 기록에 따르면 **커스텀 first broker login flow로 교체하면 기존 유저에 IdP를 자동 연결**할 수 있고,
Terraform으로도 관리할 수 있다.

## 원인

IdP 설정의 `first_broker_login_flow_alias` 가 Keycloak 기본 flow(`first broker login`)를 가리킨다.
기본 flow는 기존 계정이 있으면 바로 연결하지 않고 사용자 확인 단계를 거친다.

## 해결 방향

커스텀 flow를 만들어 IdP의 `first_broker_login_flow_alias` 를 그 flow로 바꾼다.

> **Status: 근거 미비**
> 세션 응답이 잘려 있어 flow를 어떤 authenticator로 구성했는지, 실제 적용했는지는 기록에 없다.
> 일반적으로는 기존 broker 유저를 찾는 단계 뒤에 그 유저에 자동 연결하는 단계를 두는 구성이 쓰인다.
> 이 경우 IdP가 넘기는 email을 신뢰할 수 있는지가 보안상 전제가 된다 (계정 탈취 위험).
> 공식 문서를 `raw/` 에 편입해 보강할 것.

## See Also

- [Keycloak Admin API audience 검사와 Terraform provider 인증 실패](keycloak-admin-api-audience-check.md)
- [Istio service mesh에서 JWT 인증 처리](../kubernetes/istio-jwt-authentication.md)
