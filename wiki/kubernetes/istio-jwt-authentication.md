---
title: Istio service mesh에서 JWT 인증 처리
type: article
status: verified
confidential: internal
tags: [kubernetes, istio, authentication, jwt, service-mesh]
---

# Istio service mesh에서 JWT 인증 처리

> Sources: Istio Docs; 작업 기록, 2025-05-12 ~ 2025-05-13
> Raw: [Istio L7 Network Policy](../../raw/kubernetes/istio-l7-network-policy.md); [Istio Authentication 가이드](../../raw/kubernetes/istio-authentication-guide.md)
> Updated: 2026-09-15

## Overview

Authorization 헤더의 JWT 토큰 **유효성 검사를 애플리케이션이 아니라 Istio service mesh 계층에서**
처리하는 구성이다. 각 서비스가 토큰 검증 코드를 따로 들고 있을 필요가 없어진다.

authentication service에 PoC를 적용한 것이 **2025-05-12**, 마무리한 것이 **2025-05-13**이다.

## 리소스 두 개가 짝을 이룬다

역할이 갈린다. 둘 다 있어야 의도한 대로 동작한다.

| 리소스 | 역할 |
|---|---|
| `RequestAuthentication` | 토큰을 **어떻게 검증할지** — issuer, jwksUri 지정 |
| `AuthorizationPolicy` | 검증된 결과로 **무엇을 허용할지** — 경로별 접근 제어 |

`RequestAuthentication`만 걸면 토큰이 *있을 때* 검증할 뿐, 토큰 없는 요청은 그대로 통과한다.
경로를 실제로 잠그는 건 `AuthorizationPolicy` 쪽이다.

## AuthorizationPolicy — 경로 단위로 가른다

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: stg-release-name-authentication-service-public
spec:
  selector:
    matchLabels:
      app: authentication-service-public
  rules:
    - from:
      - source:
          requestPrincipals:
          - '*'
      to:
      - operation:
          paths:
          - /api/v1/spaces/*
    - to:
      - operation:
          notPaths:
          - /api/v1/spaces/*
```

규칙 두 개가 하는 일:

1. `/api/v1/spaces/*` — `requestPrincipals: ['*']` 이므로 **유효한 JWT를 가진 요청만** 통과.
   principal이 붙으려면 `RequestAuthentication`의 검증을 통과해야 한다
2. 그 밖의 경로(`notPaths`) — 인증 요구 없이 통과

즉 **보호 대상을 화이트리스트로 지정하고 나머지는 열어두는** 형태다.
반대로(기본 차단, 예외만 허용) 가려면 두 번째 규칙을 빼야 한다.

## RequestAuthentication — 토큰 검증 방법

```yaml
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: stg-release-name-authentication-service-public
spec:
  selector:
    matchLabels:
      app: authentication-service-public
  jwtRules:
    - forwardOriginalToken: true
      issuer: https://<keycloak-host>/realms/<realm>
      jwksUri: http://<auth-service>/.well-known/jwks.json?space=<realm>
```

*issuer·jwksUri의 실제 값은 환경별로 다르다. 적용 당시 값은
[raw 기록](../../raw/kubernetes/istio-l7-network-policy.md)에 그대로 남아 있다.*

짚어둘 것:

- **`forwardOriginalToken: true`** — 검증 후에도 원본 토큰을 upstream으로 넘긴다.
  애플리케이션이 토큰 안의 claim을 여전히 써야 한다면 이 값이 필요하다
- `jwksUri`가 클러스터 내부 주소(`.svc.cluster.local`)를 가리킨다 —
  JWKS 조회가 외부로 나가지 않는다
- `jwksUri`에 `?space=` 쿼리가 붙는다. realm별로 JWKS가 갈리는 구조다

## 참고

- [RequestAuthentication](https://istio.io/latest/docs/reference/config/security/request_authentication/)
- [AuthorizationPolicy](https://istio.io/latest/docs/reference/config/security/authorization-policy/)
