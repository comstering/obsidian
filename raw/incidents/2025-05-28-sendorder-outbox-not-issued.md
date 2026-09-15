## What Happened
1. 25.05.27 14:30 주문 전송 Batch 이후 Batch에서 outbox에 발행한 event 미발행

## Impact
- 2025-05-27 15:30 ~ 2025-05-28 10:30 주문 미처리

## Resolution
- 25.05.28 10:40 legacy outbox connector 재시작을 통해서 미발행 Event 발행

## 5 Whys (Root cause)
- Event가 왜 발행되지 못했나요?
	- 서비스 비즈니스 로직에서는 정상적으로 outbox Table에 이벤트를 저장했습니다.
	- 해당 Table을 CDC하는 legacy outbox에서 CDC를 하지 못해 Event가 MSK(kafka)로 발행되지 않았습니다.
- 왜 CDC를 못했나요?
	- 원인 파악에 어려움이 있습니다.
		- CDC가 멈춘 환경을 다시 재현하기가 힘든 상황입니다.
		- Dev에서 동일하게 legacy Dev DB를 outbox CDC하고 있는 connector는 현재까지도 정상적으로 heartbeat를 발행중입니다.
- 그러면 Event가 발행되지 않고 있는 상황을 빠르게 인지하지 못했나요?
	- debezium connector의 status가 running/healthy 상태로 유지 중이었기에 connector가 문제가 있는 상황으로 판단하지 않았습니다.
- Event가 발행되고 있지 않는 문제 상황인데 왜 healthy 상태인가요?
	- kafka connect에서 해당 connector가 Failed 상태가 되는 상태는 connector 자체에서 실제로 Exception이 throw 되었을 때 중지됩니다. debezium connector에서 throw Exception이 발생하지 않으면 계속 running 상태로 남아있습니다.
- 왜 Exception이 발생하지 않았나요?
	- 위에서 원인파악에 어려움 있는 부분과 동일합니다.
		- DB와의 connection이 끊기는 상황으로 예상하고 있지만 실질적인 재현을 할 수 없는 상황입니다.
		- 의심 point
			- kafka connect 내부 로직 처리 중 task 내부 쓰레드 hang
			- legacy DB와의 connection 처리 오류
			- binlog reader hang -> TCP 연결은 살아있으나 stream 멈춤

## What went Well?
- binlog를 통한 CDC로 인해 미발행된 이벤트가 발생했지만 Data 유실 없이 없었습니다.
	- connector를 Restart하고 미발행된 이벤트 Data 모두 정상발행되었습니다.
## What didn't go so well?
- 인지 후 빠른 조치를 진행해야하는데 조치가 늦어졌습니다.
	- event 미발행 인지 후 connector에서의 미발행원인을 파악하고 재시작하는 시점까지 40분가량 발생했습니다.
## Action Items
- 중요 topic들 메세지 발행량 지표 이상 탐지 alert monitor 추가
	- 중요 비즈니스 topic 
	- debezium connector heartbeat topic https://app.datadoghq.com/monitors/173397381
- Runbook
	- CDC 불가 문제의 대부분은 Connector Restart를 통해서 해결 가능 (관련 Runbook 작성)
- debezium connector errors.max.retries 기본값: -1 => 무한 retry
	- 현재 debezium connector의 기본 값으로 사용 중입니다.
	- retry를 진행하고 있을 경우 connector의 상태는 running/healthy로 유지됩니다.
	- kafka connect task 내부 문제로 인한 장애 시 빠른 인지가 가능합니다.
		- retries 횟수를 넘으면 connector를 Failed 상태로 변경합니다.
		- 현재 connector가 Failed가 되면 Alert 메시지를 발행하는 Monitor가 추가되어 있습니다.
			- https://app.datadoghq.com/monitors/167317629
		- 조치 방법은 connector Restart가 가장 빠른 해결 방안입니다.
	- retry vs. restart

| 항목               | Retry                                     | Connector Restart                           |
| ---------------- | ----------------------------------------- | ------------------------------------------- |
| **수행 주체**        | Debezium connector 내부                     | Kafka Connect framework 또는 운영자              |
| **기준**           | recoverable error 감지 시 내부에서 자동            | 명시적인 외부 API 호출 또는 Pod 재시작 등                 |
| **영향 범위**        | 해당 task 내부 스레드 재시작                        | task process 자체 종료 및 재시작                    |
| **offset 유지 여부** | ✅ 기존 offset 유지 (resume)                   | ✅ 기본적으로 유지되나, 설정 따라 snapshot 재개 가능성 있음      |
| **재연결 대상**       | MySQL JDBC, binlog client, Kafka producer | 전체 connector lifecycle 재시작 (모든 구성요소 재생성)    |
| **구현 수준**        | Debezium 코드 내부                            | Kafka Connect REST API 수준 or 시스템적 수준        |
| **복구 가능 범위**     | 일시적 네트워크, 권한 오류 등                         | retry로는 복구 불가능한 내부 hang, thread leak 등까지 가능 |

## Timeline
| Time             | Summery                                         | Detail |
| ---------------- | ----------------------------------------------- | ------ |
| 25.05.27 14:30   | 주문 전송 Batch                                     |        |
| 25.05.27 14:30   | Outbox Event 발행                                 |        |
| 25.05.27 15:30 ~ | 주문 전송 Batch                                     |        |
| 25.05.27 15:15   | legacy outbox heartbeat event 미발행               |        |
| 25.05.27 15:30 ~ | Outbox Event 미발행                                |        |
| 25.05.28 10:00   | 김동현(글로벌 SCM팀)님 GMS 미연동 이슈 Alert                 |        |
| 25.05.28 10:40   | legacy outbox connector restart                 |        |
| 25.05.28 10:44   | legacy outbox connector running and event issue |        |
![[스크린샷 2025-05-28 오후 3.33.07.png]]