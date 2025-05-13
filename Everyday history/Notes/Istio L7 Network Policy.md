
#### RequestAuthentication
- https://istio.io/latest/docs/reference/config/security/request_authentication/
#### AuthorizationPolicy
- https://istio.io/latest/docs/reference/config/security/authorization-policy/

- authentication service PoC 적용(2025-05-12)
	- 내일 조금 더 확인 필요

- 마무리 완료 (2025-05-13)

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
      issuer: https://dev-keycloak.private.oliveyoung.com/realms/globalone-partner  
      jwksUri: http://dev-authentication-service-private.app.svc.cluster.local/.well-known/jwks.json?space=globalone-partner
```


