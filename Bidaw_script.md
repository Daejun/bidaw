# Bidaw 세미나 발표 스크립트 (50분)

논문: **Bidaw: Enhancing Key-Value Caching for Interactive LLM Serving via Bidirectional Computation–Storage Awareness** — Hu et al., FAST '26

> 사용 방법
> - 각 슬라이드 블록의 *핵심 메시지*는 청중이 그 슬라이드에서 단 한 가지만 가져갔으면 하는 문장이다. 발표 중 한 번은 그대로 말한다.
> - *짚을 점*은 그 슬라이드에서 다룰 내용이다. 그대로 읽지 말고 자기 말로 옮긴다.
> - *이어가기*는 다음 슬라이드로 넘어가기 직전의 한 호흡 멘트.
> - 각 섹션 머리의 `[X분]`은 누적 시간이 아니라 **이 섹션에 쓰는 분량**.

---

## Part 1. Opening — 3분

### Slide 1. Title — `0:00–0:30` (30초)
- **핵심 메시지**: 오늘 다룰 논문은 FAST '26의 *Bidaw*. KV 캐싱에서 compute와 storage가 서로의 정보를 보게 만드는 시스템이다.
- **짚을 점**
  - 논문 출처와 저자 소속을 짧게. Tsinghua와 China Telecom 공동 — 실서비스 trace가 강점인 논문이라는 인상을 미리 준다.
  - 핵심 키워드 두 개만 미리 던지기: *interactive LLM serving*, *bidirectional awareness*.
- **이어가기**: 50분 동안 무엇을 다룰지부터 보겠습니다.

### Slide 2. Agenda — `0:30–3:00` (2분 30초)
- **핵심 메시지**: 메커니즘 3개와 평가 1개, 각각이 이 논문의 독립된 기여다.
- **짚을 점**
  - 8개 항목 중 *Mechanism 1, 2, 3*이 이 논문의 핵심 기여.
  - 평가는 모델 5종 + 자체 trace + ShareGPT — 폭이 넓다.
  - 마지막에 한계와 일반화 가능성을 *반드시* 짚겠다는 약속을 먼저 한다.
- **이어가기**: 우선 배경부터. interactive LLM serving이 정확히 무엇인지 합을 맞추겠습니다.

---

## Part 2. Background — 8분

### Slide 3. Interactive LLM serving — `3:00–4:30` (1분 30초)
- **핵심 메시지**: 사용자 한 명이 *수십 번* 라운드를 주고받는다는 사실이 이 논문의 모든 설계 결정의 출발점이다.
- **짚을 점**
  - 응용 예: Replika, Duolingo Max, 고객 응대 챗봇.
  - 사용자 한 명당 평균 22.4 라운드, P90이 45 라운드 — ShareGPT 평균 5.7과 비교해 *4배 이상* 길다.
  - 라운드 N의 답변이 0~N-1 라운드의 *모든* KV에 의존한다는 점을 Figure 1로 짚는다.
- **이어가기**: 그렇다면 이 KV가 정확히 무엇이고, 왜 캐싱해야 하는지 짧게 합을 맞춥니다.

### Slide 4. KV cache 역할 — `4:30–6:30` (2분)
- **핵심 메시지**: KV cache는 attention 재계산을 피하는 *유일한* 수단이고, 크기는 토큰 수에 비례해 늘어난다.
- **짚을 점**
  - `softmax(Q·Kᵀ/√d)·V` 한 줄로 핵심만 짚되, 청중에 따라 가볍게 흘려보내지 말 것.
  - 새 토큰의 Q만 새로 계산되고 과거 K, V는 그대로 — "재사용해도 수학적으로 동일하다"를 강조한다.
  - OPT-13B에서 2,048 토큰이면 약 0.78 GB / user — 이 숫자를 외워두면 뒤의 perf layer 200 GB 논의로 자연스럽게 이어진다.
- **이어가기**: 그렇다면 이 KV가 GPU에 다 들어가느냐 — 안 들어간다. 그게 이 논문의 출발선이다.

### Slide 5. 왜 GPU 메모리에 다 담을 수 없는가 — `6:30–8:00` (1분 30초)
- **핵심 메시지**: 사용자가 30명/분만 도착해도 동시 캐싱 KV가 host memory(perf layer)도 *3.91배 초과*한다.
- **짚을 점**
  - 80 GB GPU와 host memory(GPU의 1.6~3.2배)를 곱해도 200~250 GB 범위.
  - Figure 5의 *수평선 200 GB*가 바로 perf layer. 도착률 10 users/min 정도부터 이미 넘는다.
  - "그래서 SSD까지 쓰는 2-tier가 등장했다"로 다음 슬라이드와 자연스럽게 연결.
- **이어가기**: 기존 솔루션이 어떻게 생겼는지 잠깐 보고 가겠습니다.

### Slide 6. Two-tier storage — `8:00–9:30` (1분 30초)
- **핵심 메시지**: CachedAttention과 FlashGen 같은 직전 SOTA는 *write*는 critical path에서 빼냈지만, *read*는 여전히 critical path 위에 남아 있다.
- **짚을 점**
  - Figure 2 — perf layer는 host DRAM, capacity layer는 SSD.
  - CachedAttention(ATC '24)과 FlashGen(FAST '25)이 직전 SOTA. Bidaw는 이 둘을 베이스라인으로 삼는다.
  - 이 논문이 정확히 겨냥하는 지점은 "load 경로의 비효율".
- **이어가기**: 그 비효율이 얼마나 큰지 숫자로 확인합니다.

### Slide 7. KV loading이 곧 critical path — `9:30–11:00` (1분 30초)
- **핵심 메시지**: 모든 KV가 perf layer에 있다고 *가정한* ideal과 비교했을 때 latency가 *3.8배*, throughput이 *2배* 격차가 난다.
- **짚을 점**
  - Figure 3의 빨간 "Gap" 화살표를 짚는다 — 이 논문이 메우려는 격차.
  - 같은 환경에서 OPT-13B + 200 GB host + 1.5 GB/s SSD라는 점을 못 박아둔다. 평가 슬라이드와 정확히 일치.
  - "왜 이렇게 큰 격차가 생기는가?"로 motivation 섹션을 연다.
- **이어가기**: 이 격차의 *근본 원인*을 찾기 위해 실서비스 trace로 워크로드를 직접 들여다보겠습니다.

---

## Part 3. Motivation — 8분

### Slide 8. 워크로드 소개 — `11:00–13:00` (2분)
- **핵심 메시지**: 이 논문이 쓴 워크로드는 *기존 공개 trace에는 없는* 형태다. 사용자 단위 timestamp가 보존된 100만+ 라운드 trace.
- **짚을 점**
  - China Telecom omni-channel center에서 받은 100만+ 라운드.
  - ShareGPT는 라운드 수 5.7로 너무 짧고, Mooncake는 토큰은 길지만 대화 패턴이 없다.
  - 이 trace가 *interactive*의 정의에 가장 잘 맞는다. 여기서만 보이는 세 가지 관찰을 이어지는 슬라이드에서 다룬다고 예고.
- **이어가기**: 첫 번째 관찰 — 동시에 캐싱되어 있어야 할 KV의 총량.

### Slide 9. Observation 1 — `13:00–15:00` (2분)
- **핵심 메시지**: 한 사용자의 KV가 22.4 라운드 동안 살아있어야 하므로, 도착률이 오르면 동시 KV 총량이 *perf layer를 그대로 넘어버린다*.
- **짚을 점**
  - Figure 5 — 30 users/min에서 OPT-13B의 KV 총량이 480 GB. 200 GB perf layer의 2.4배.
  - "perf layer를 키우면 되지 않나?"에 대한 답: GPU 서버 host memory는 보통 GPU 메모리의 1.6~3.2배로 묶여 있다.
  - 결국 *eviction이 자주 트리거된다*는 뜻을 강조한다.
- **이어가기**: eviction이 자주 일어나는 건 알겠는데, 다시 들어올 때 hit rate은 어떨까?

### Slide 10. Observation 2 — `15:00–17:00` (2분)
- **핵심 메시지**: KV access의 *temporal locality가 약하다*. 80%의 access가 perf layer 크기를 넘어서고, 어떤 정책도 hit rate가 20% 수준에 머무른다.
- **짚을 점**
  - *Weighted reuse distance*의 정의 — "두 access 사이에 끼어든 다른 KV들의 크기 합"을 천천히 짚는다. 여기서 청중이 못 따라오면 뒤의 eviction 알고리즘이 무너진다.
  - Figure 6(b) — FIFO, LRU, queue-enhanced 모두 ~20% hit. perf layer가 KV의 40.1%를 담을 수 있는데도 절반 수준.
  - 왜 약한가? 사용자가 *다음 질문을 생각하는 시간* 동안 다른 사용자 요청이 계속 끼어들기 때문.
- **이어가기**: 도착률이 클 뿐 아니라, 도착하는 *각 요청*도 균일하지 않다.

### Slide 11. Observation 3 — `17:00–19:00` (2분)
- **핵심 메시지**: KV loading 시간의 *변동계수가 5초 윈도우 안에서도 90%를 넘는다*. 큰 KV 하나가 뒤따르는 작은 KV들까지 막아버린다.
- **짚을 점**
  - 두 가지 원인: (a) host DRAM과 SSD의 대역폭 격차, (b) KV size 자체가 수십 MB에서 수백 MB까지 다양 (Figure 8).
  - 결과는 head-of-line blocking. FCFS면 큰 capacity-layer KV 하나가 *수백 ms* 동안 GPU를 놀게 만든다.
  - 곧 이 논문 *Mechanism 1*이 풀려는 문제다.
- **이어가기**: 세 가지 관찰을 종합하면 root cause가 한 줄로 정리됩니다.

---

## Part 4. Root Cause & Key Idea — 4분

### Slide 12. Root cause — `19:00–21:00` (2분)
- **핵심 메시지**: 두 문제 모두 *compute와 storage 사이에서 정보가 한쪽으로만 흐르거나 아예 끊겨 있어서* 생긴다.
- **짚을 점**
  - 문제 1: compute가 storage I/O 시간을 모른다 → FCFS dispatch가 head-of-line blocking을 만든다.
  - 문제 2: storage가 사용자 대화 패턴을 모른다 → eviction이 storage 측 history만 본다.
  - 두 문제는 본질적으로 *대칭*이다. 두 시스템이 서로를 못 본다는 한 원인의 두 얼굴.
- **이어가기**: 그래서 이 논문의 답은 "양방향으로 정보를 흐르게 한다" — bidirectional awareness.

### Slide 13. Key idea — `21:00–23:00` (2분)
- **핵심 메시지**: Compute → Storage로는 *답변 길이*를, Storage → Compute로는 *KV 위치와 크기*를 흘려보낸다.
- **짚을 점**
  - 답변 길이가 왜 의미 있는가? 사용자가 답변을 *읽는 시간*을 결정하므로, 그 사이 끼어들 다른 사용자 KV의 양을 가늠할 수 있다.
  - KV 위치와 크기는 storage 입장에서 자명한 정보. 기존 시스템들이 이걸 compute로 *내보내지* 않았을 뿐이다.
  - 이 두 신호에서 두 메커니즘이 나온다 — 그게 이어지는 11장이다.
- **이어가기**: 시스템 그림으로 한눈에 보겠습니다.

---

## Part 5. System Overview — 3분

### Slide 14. 아키텍처 — `23:00–24:30` (1분 30초)
- **핵심 메시지**: Bidaw = Scheduler + History Cacher + Eviction Manager. 세 컴포넌트가 두 신호를 주고받는다.
- **짚을 점**
  - Figure 9의 ①②③④ 화살표를 시계 방향으로 따라간다.
  - 빨간 점선이 storage 경계 — 이 경계를 넘는 두 신호가 핵심.
  - History Cacher(§4)는 Mechanism 3에서 다룬다고 미리 알린다.
- **이어가기**: 동작 순서를 좀 더 명확히 보겠습니다.

### Slide 15. Workflow — `24:30–26:00` (1분 30초)
- **핵심 메시지**: 4단계 — dispatch → inference → answer length 전달 → threshold 기반 eviction.
- **짚을 점**
  - ① Scheduler dispatch는 §3.2.
  - ② History Cacher가 *KV tensor 자체*가 아니라 *storage-efficient tensor*를 잡는다는 점이 새롭다(§4).
  - ③ 답변이 끝나는 즉시 길이를 Eviction Manager로 — 정보를 *바로* 흘려보낸다.
  - ④ 여유 공간이 5% 미만이면 트리거 → 백그라운드에서 hit potential을 계산해 evict.
- **이어가기**: 이제 첫 번째 메커니즘부터 들어갑니다.

---

## Part 6. Mechanism 1 — I/O-aware Scheduling — 7분

### Slide 16. I/O blocking 문제 — `26:00–28:00` (2분)
- **핵심 메시지**: GPU iteration(수십 ms)이 capacity-layer I/O(수백 ms)보다 훨씬 짧기 때문에 *단순한 overlap만으로는 부족하다*.
- **짚을 점**
  - Overlap의 한계: 다음 layer KV load와 현재 layer compute가 겹치는 만큼만 가려진다.
  - 그래서 *큐 자체*를 다시 짜야 한다는 것이 설계 목표.
  - "큰 KV는 굶지 않고, 작은 KV는 막히지 않게" — 이 두 조건을 동시에 맞춰야 한다.
- **이어가기**: 두 조건을 어떻게 함께 맞추는지 보겠습니다.

### Slide 17. Dual queue + disk-HRRN — `28:00–31:00` (3분)
- **핵심 메시지**: *Dual queue*가 빠른 I/O와 느린 I/O를 갈라놓고, *disk-HRRN*이 큰 KV의 starvation을 막는다.
- **짚을 점**
  - Ready queue: KV가 perf layer에 있는 요청 — FCFS로 GPU에 바로 보낸다.
  - Preparing queue: capacity layer 요청 — 백그라운드로 perf layer에 끌어올린다.
  - **disk-HRRN 식**을 칠판처럼 천천히: `R = 1 + waiting / size`.
    - waiting이 길어지면 큰 KV도 결국 ratio가 올라간다 → starvation 방지.
    - size가 작으면 ratio가 처음부터 높다 → 빠르게 promote.
  - Promotion 후에도 *원래 도착 시각을 그대로 유지*하는 디테일을 강조 — tail latency 급증을 막는 장치다.
- **이어가기**: 그림으로 보면 차이가 더 명확합니다.

### Slide 18. 동작 예시 — `31:00–33:00` (2분)
- **핵심 메시지**: 같은 5개 요청이라도 FCFS는 GPU를 *반쯤 놀게* 두지만, I/O-aware는 그 시간을 채운다.
- **짚을 점**
  - Figure 11(a): 큰 KV(req 1, 2)가 큐 앞을 막아 뒤의 req 3, 4, 5의 perf-layer hit까지 같이 막힌다.
  - Figure 11(b): req 3, 4, 5가 먼저 GPU로 가고, 그 사이 req 2가 promote된다.
  - 평균 큐잉 시간 5.76초 → 2.45초, *57.5% 단축*.
- **이어가기**: 여기까지가 compute 측. 다음은 storage 측 — eviction.

---

## Part 7. Mechanism 2 — Previous-answer-based Eviction — 8분

### Slide 19. Reuse distance와 answer length — `33:00–35:00` (2분)
- **핵심 메시지**: 이전 라운드 답변이 길수록 다음 KV access의 *weighted reuse distance 하한*이 함께 증가한다 (Spearman ρ = 0.94 ~ 0.98).
- **짚을 점**
  - Figure 12 — 12개 시간대 모두에서 같은 패턴이 나온다. *robustness*에 대한 강한 증거.
  - 직관: 답변이 길면 사용자가 더 오래 읽는다 → 그 사이 다른 사용자 KV가 끼어든다 → reuse distance가 커진다.
  - 이건 *human-in-the-loop* 워크로드에 본질적으로 깔린 신호. 다른 도메인으로의 일반화 가능성을 잠깐 언급한다.
- **이어가기**: 그러나 reuse distance가 크다고 무조건 evict해도 되는 건 아니다.

### Slide 20. Hit potential — `35:00–37:00` (2분)
- **핵심 메시지**: Reuse distance가 *promising 영역*에 있는 access는 LRU에서 hit이 거의 0이지만, *Belady에서는 100%* 가까이 살아 있다.
- **짚을 점**
  - Figure 13의 세 영역: small / promising / extreme.
  - 핵심은 *promising 구간*이다 — LRU와 queue-enhanced가 약한 지점이 여기다.
  - 따라서 단순한 거리 기반 evict가 아니라, *구간별 hit 확률을 추정*하는 알고리즘이 필요하다.
- **이어가기**: 그러면 구간별 hit 확률은 어떻게 추정할까?

### Slide 21. Ghost cache + bucketing — `37:00–39:00` (2분)
- **핵심 메시지**: Promising 영역을 *m개 fine-grained bucket*으로 나누고, 각 bucket의 hit 확률을 *백그라운드 Belady 시뮬레이션*으로 측정한다.
- **짚을 점**
  - 5단계 알고리즘을 그대로 따라간다.
  - *Ghost cache*는 실제 데이터 없이 metadata만 관리한다 — 그래서 Belady가 현실에서 "feasible"해진다.
  - 사용자별 과거 분포로 다음 access가 떨어질 bucket 확률을 추정한다.
  - *compute가 보낸 답변 길이*로 lower bound를 정해 더 작은 bucket의 확률을 0으로 truncate — 이 부분이 bidirectional 신호의 결정적인 활용점이다.
- **이어가기**: 마지막으로 결정식을 봅니다.

### Slide 22. Equation 2 — `39:00–41:00` (2분)
- **핵심 메시지**: 한 줄짜리 *Overall_potential* 식이 small, promising bucket들, extreme의 가중합으로 evict 후보를 결정한다.
- **짚을 점**
  - 세 항을 하나씩: *prob_small × 1.0*, *Σ prob_promising(i) × hit_promising(i)*, *prob_extreme × 0.0*.
  - potential이 가장 낮은 KV가 evict 대상이다.
  - 추가 비용은 *0.35 ms* — 무거운 일은 백그라운드에서 ghost cache가 다 한다는 점을 강조한다.
- **이어가기**: 이제 마지막 메커니즘 — 어떤 tensor를 캐싱할지.

---

## Part 8. Mechanism 3 — Storage-Efficient Tensor — 3분

### Slide 23. Tensor cost efficiency — `41:00–42:30` (1분 30초)
- **핵심 메시지**: KV tensor를 캐싱하는 건 *최선이 아니다*. 정규화된 activation(tensor 6)이 *cost efficiency 51 GFLOPs/MB*로 KV(30.5)의 1.67배.
- **짚을 점**
  - 새 metric *cost efficiency = saved compute / required space*를 정의한다.
  - Figure 14(b) — tensor 6에서 곡선이 정점을 찍는다.
  - Tensor 6에서 KV로 되돌리는 변환은 *GPU 1 step*이면 끝 — overhead가 작다.
- **이어가기**: 그럼 모든 모델에 이득일까? 그렇지 않다.

### Slide 24. MHA vs GQA — `42:30–44:00` (1분 30초)
- **핵심 메시지**: MHA에서는 tensor 6 캐싱이 이득이고, *GQA에서는 KV tensor 자체가 이미 작으니 그대로 캐싱한다*.
- **짚을 점**
  - MHA: head마다 K, V가 분리 → KV가 크다 → tensor 6가 유리.
  - GQA: 여러 query head가 K, V를 공유 → KV 자체가 작음 → 변환 비용이 이점을 깎아먹는다.
  - Llama, Qwen, Bloom, OPT, Baichuan은 MHA — 따라서 이 논문 평가 모델 대부분에서 적용된다.
- **이어가기**: 구현 디테일을 짧게.

---

## Part 9. Implementation — 1분

### Slide 25. 구현 노트 — `44:00–45:00` (1분)
- **핵심 메시지**: vLLM 위에 네 가지 기법 — continuous batching, mix-grained PagedAttention, low-priority CUDA stream, inclusive caching.
- **짚을 점**
  - **Mix-grained PagedAttention** 디테일이 흥미롭다: history와 query는 256 토큰의 큰 블록, response는 16 토큰의 작은 블록. CPU-GPU 전송 효율도 올라가고 단편화도 줄어든다.
  - Storage-efficient tensor → KV 변환은 *low-priority CUDA stream*에서 처리한다 — 실제 추론 latency에 영향이 없다.
  - Inclusive caching으로 eviction이 *write-free* — 큰 SSD write 트래픽이 생기지 않는다.
- **이어가기**: 그래서 평가 결과는?

---

## Part 10. Evaluation — 5분

### Slide 26. 실험 환경 — `45:00–46:00` (1분)
- **핵심 메시지**: 모델 5종(OPT 6.7B/13B/30B, Qwen 7B/14B), 자체 trace + ShareGPT, baseline 4종.
- **짚을 점**
  - vLLM은 recompute baseline. CachedAttention과 FlashGen은 KV-caching SOTA. Optimal은 perf-layer-only ideal.
  - 하드웨어는 보수적으로 잡았다 — 1.5 GB/s SSD. PCIe 4.0이라 GPU 전송은 30 GB/s 정도 — 즉 *SSD가 진짜 bottleneck*임을 강조한다.
- **이어가기**: 핵심 그림을 봅니다.

### Slide 27. Overall performance — `46:00–47:30` (1분 30초)
- **핵심 메시지**: 모델 5종 모두에서 Bidaw가 *Optimal에 거의 붙는다* — latency 최대 3.58배 단축, throughput 1.83배 향상.
- **짚을 점**
  - Figure 15에서 모든 패널의 Bidaw 곡선이 Optimal과 거의 평행하다.
  - 같은 latency 기준의 throughput 비교가 핵심 — *얼마나 더 많은 user/min*을 받을 수 있는가.
  - Bidaw는 *lossless* — 답변 정확도는 FlashGen과 동일하다. 답변 순서만 바뀌므로 LLM 출력은 그대로다.
- **이어가기**: 다른 축에서도 확인하겠습니다.

### Slide 28. Memory sensitivity와 miss rate — `47:30–48:30` (1분)
- **핵심 메시지**: host memory가 작을수록 *격차가 더 벌어진다* — 메모리 절약 측면에서 진짜 가치가 드러난다.
- **짚을 점**
  - Figure 16 — host memory 120 GB만으로도 Bidaw가 baseline의 200 GB 수준 latency를 낸다. 1.75~2.19배의 user/min을 지원.
  - Figure 18 — eviction miss rate가 queue-enhanced 대비 -57.6%, FIFO/LRU 대비 -69.9%.
- **이어가기**: 마지막으로 tail latency와 내부 분해.

### Slide 29. Tail · Ablation · Overhead — `48:30–50:00` (1분 30초)
- **핵심 메시지**: P99까지 단축, 세 메커니즘이 곱셈으로 기여, overhead는 ms 단위로 무시할 수 있다.
- **짚을 점**
  - Tail: CachedAttention 대비 P90 −53%, P95 −49%, P99 −47% — 평균뿐 아니라 *분포의 꼬리*까지 잡았다.
  - Ablation: scheduling 1.58배, eviction 1.25배, tensor caching 1.10배 — 각 메커니즘이 *독립적으로 의미가 있다*.
  - Overhead: scheduling 0.62 ms, eviction 0.35 ms, KV 변환 < 100 ms — 시스템에 안전하게 얹을 수 있다.
- **이어가기**: 마무리하겠습니다.

---

## Part 11. Conclusion & Discussion — 3분

### Slide 30. 정리 · 한계 · 시사점 — `50:00 이후 Q&A 직전` (마지막 3분)
- **핵심 메시지**: Bidaw의 진짜 기여는 "compute와 storage가 *양방향으로* 서로의 정보를 본다"는 *설계 원칙*이다. 알고리즘 디테일은 그 원칙을 구체화한 결과다.
- **짚을 점**
  - **기여**
    - Bidirectional awareness라는 새로운 설계 원칙.
    - I/O-aware scheduling과 previous-answer-based eviction 두 메커니즘.
    - Storage-efficient tensor caching으로 공간과 연산의 trade-off를 정량화.
    - 모델 5종에서 평균 latency 3.58배, throughput 1.83배.
  - **한계**
    - 한 사용자 안에서의 KV 재사용만 다룬다 — *사용자 간 KV 공유*는 범위 밖 (MeanCache 계열과 직교).
    - GQA에서는 storage-efficient tensor의 이점이 사라진다.
    - ShareGPT처럼 timestamp가 없는 trace에서는 eviction 효과가 약해진다 (논문도 인정).
    - 단일 GPU 노드 평가 — disaggregated 또는 multi-node 환경은 future work.
  - **시사점**
    - 사용자가 글을 읽는 속도를 storage 정책의 *신호*로 쓸 수 있다는 일반적인 교훈.
    - HRRN과 Belady ghost cache 같은 고전 기법이 LLM 워크로드에서도 여전히 유효함을 보였다.
    - ML serving과 storage의 co-design 사례 — 이 영역의 후속 연구가 활발해질 것이다.
- **이어가기**: "여기까지가 Bidaw입니다. 질문 받겠습니다."

---

## 발표 팁 (사전 리허설용)

- **숫자는 외워둘 것**: 3.8배 / 2.0배 (gap), 22.4 (round), 80% / 20% (locality), 51 vs 30.5 (cost eff), 3.58배 / 1.83배 (final).
- **잘못 쓰기 쉬운 용어**: *weighted* reuse distance — 그냥 reuse distance가 아니라 *byte 합*이다. 일찍 정의해두지 않으면 §3.3 전체가 흔들린다.
- **놓치기 쉬운 디테일**
  - HRRN의 변형이 disk-HRRN — *I/O 시간 ≈ KV size*라는 가정이 깔려 있다.
  - Inclusive caching이 큰 write traffic을 막는다 — eviction 비용이 거의 0이 되는 이유다.
- **질문 대비**
  - "GQA에서는?" → tensor caching은 비활성. 나머지 두 메커니즘은 그대로 적용된다.
  - "왜 답변 길이가 신호로 충분한가?" → 사용자가 답을 다 읽고 다음 질문을 만들기까지 *최소 시간 하한*을 만들기 때문이다.
  - "ShareGPT에서는 왜 효과가 약해지나?" → timestamp 시뮬레이션이 Poisson이라 답변 길이와 사용자가 머뭇거리는 시간이 분리되기 때문이다.
  - "Bidaw가 lossless인가?" → 답변 정확도는 그대로다. user 1과 user 2의 처리 *순서*만 바뀔 뿐, LLM 출력은 같다.
