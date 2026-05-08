# Bidaw 세미나 발표 스크립트 (50분)

논문: **Bidaw: Enhancing Key-Value Caching for Interactive LLM Serving via Bidirectional Computation–Storage Awareness** — Hu et al., FAST '26

> 사용 방법
> - 각 슬라이드 블록의 *Key message*는 청중이 그 슬라이드에서 단 하나만 가져갔으면 하는 문장이다. 발표 중 한 번은 명시적으로 말한다.
> - *Talk points*는 그 슬라이드에서 짚을 항목들. 그대로 읽지 말고 자기 표현으로 말한다.
> - *Transition*은 다음 슬라이드로 넘어가기 직전 한 호흡 멘트.
> - 각 섹션의 머리에 `[X분]`은 누적 시간이 아니라 **이 섹션에 쓰는 분량**.

---

## Part 1. Opening — 3분

### Slide 1. Title — `0:00–0:30` (30초)
- **Key message**: 오늘 다룰 논문은 FAST '26의 *Bidaw*, KV 캐싱을 *compute*와 *storage*가 서로 들여다보게 만드는 시스템이다.
- **Talk points**
  - 논문 출처와 저자 소속 간단히 (Tsinghua + China Telecom — 산업체 trace가 강한 논문이라 강조).
  - 핵심 키워드 두 개만 미리 등장: *interactive LLM serving*, *bidirectional awareness*.
- **Transition**: 50분 동안 무엇을 다루는지 먼저 보겠습니다.

### Slide 2. Agenda — `0:30–3:00` (2분 30초)
- **Key message**: 3개 메커니즘과 1개의 평가가 있고, 각각이 본 논문의 다른 contribution이다.
- **Talk points**
  - 슬라이드의 8개 항목 중 *Mechanism 1, 2, 3* 이 본 논문의 핵심 contribution.
  - 평가는 5개 모델 + 자체 trace + ShareGPT 위에서 — 폭이 넓다.
  - 마지막에 한계 / 일반화 가능성을 *반드시* 다룬다는 것을 미리 약속.
- **Transition**: 우선 배경부터. interactive LLM serving이라는 워크로드가 정확히 무엇인지 정렬을 맞추겠습니다.

---

## Part 2. Background — 8분

### Slide 3. Interactive LLM serving — `3:00–4:30` (1분 30초)
- **Key message**: 하루치 워크로드가 한 사용자당 *수십 번*의 라운드로 이루어진다는 점이 본 논문의 모든 결정에 영향을 준다.
- **Talk points**
  - 응용: Replika, Duolingo Max, 고객 응대 챗봇.
  - 평균 22.4 라운드, P90 = 45 라운드는 ShareGPT(평균 5.7)와 비교해 *4배 이상*.
  - 한 라운드의 답변은 이전 *모든* 라운드의 KV에 의존한다는 점을 Figure 1로 시각화.
- **Transition**: 이 KV가 정확히 무엇이고 왜 캐싱해야 하는지 잠깐 정렬.

### Slide 4. KV cache의 역할 — `4:30–6:30` (2분)
- **Key message**: KV cache는 attention 재계산을 막는 *유일한* 메커니즘이고, 그 크기는 토큰 수에 *선형*으로 늘어난다.
- **Talk points**
  - `softmax(QKᵀ/√d)·V` 한 줄로 핵심만 짚는다 — 청중에 따라 대수롭지 않다는 인상을 주지 말 것.
  - 새 토큰의 Q만 새로 계산되고 과거 K, V는 그대로 → "재사용해도 수학적으로 동일"임을 강조.
  - OPT-13B, 2,048 토큰 ≈ 0.78 GB / user — 이 값을 외워둘 것. 나중에 perf-layer 200GB 계산이 그대로 이어진다.
- **Transition**: 그러면 이 KV가 GPU에 다 들어갈까? 아니다. 이게 본 논문의 출발선이다.

### Slide 5. 왜 GPU 메모리에 다 못 두는가 — `6:30–8:00` (1분 30초)
- **Key message**: 사용자 도착률이 30/min만 넘어가도 동시 캐시 KV가 host memory(perf layer)도 *3.91× 초과*.
- **Talk points**
  - 80GB GPU vs. 1.6–3.2× host memory: 곱해도 200–250 GB 범위.
  - Figure 5의 *수평선 200GB*가 곧 perf layer. 도착률 10 users/min 정도부터 이미 초과.
  - "그래서 SSD로 쏟아붓는 2-tier가 등장했다"는 다음 슬라이드로 자연스럽게.
- **Transition**: 이미 나와 있는 솔루션이 어떻게 생겼는지 한 번 보고 가겠습니다.

### Slide 6. Two-tier storage — `8:00–9:30` (1분 30초)
- **Key message**: CachedAttention/FlashGen 같은 기존 시스템들은 *write*를 critical path에서 빼냈지만, *read*는 그대로 critical path 위에 있다.
- **Talk points**
  - Figure 2 그림 — perf layer는 host DRAM, capacity layer는 SSD.
  - CachedAttention(ATC '24)와 FlashGen(FAST '25)이 직전 SOTA. Bidaw는 이 둘을 baseline으로 본다.
  - 본 논문이 노리는 위치: "load 경로의 비효율성".
- **Transition**: 그 비효율이 얼마나 큰지 숫자로 보겠습니다.

### Slide 7. KV loading은 critical path — `9:30–11:00` (1분 30초)
- **Key message**: 모든 KV가 perf layer에 있다고 *가정*한 ideal과 비교했을 때 *3.8× latency / 2× throughput* 격차.
- **Talk points**
  - Figure 3의 빨간 "Gap" 화살표를 짚는다 — 이게 본 논문이 채우려는 갭.
  - 같은 환경에서 OPT-13B + 200GB host + 1.5GB/s SSD라는 점을 못 박아둔다 (평가 슬라이드와 일치).
  - "왜 이렇게 큰 격차가 나는가?" 라는 질문으로 motivation 섹션으로 넘어간다.
- **Transition**: 이 격차의 *근본 원인*을 찾기 위해 산업체 trace로 워크로드 자체를 들여다봅시다.

---

## Part 3. Motivation — 8분

### Slide 8. 워크로드 소개 — `11:00–13:00` (2분)
- **Key message**: 이 논문의 워크로드는 *기존 공개 trace에는 없는* 것이다 — 사용자 단위 timestamp + 평균 22.4 라운드.
- **Talk points**
  - China Telecom omni-channel center의 1M+ 라운드.
  - ShareGPT는 라운드 수 5.7로 너무 짧음. Mooncake는 토큰은 길지만 대화 패턴이 없음.
  - 이 trace가 *interactive*의 정의에 가장 부합. 이 워크로드 위에서만 보이는 세 가지 관찰을 다음 세 슬라이드에서 다룬다고 예고.
- **Transition**: 첫 번째 관찰 — 동시에 캐싱돼 있어야 할 KV의 양.

### Slide 9. Observation 1 — `13:00–15:00` (2분)
- **Key message**: 22.4 라운드 동안 KV가 살아있어야 하므로, 도착률이 늘면 동시 KV 총량이 *perf layer를 그냥 넘어버린다*.
- **Talk points**
  - Figure 5 — 30 users/min일 때 OPT-13B의 KV 총량 480GB. 200GB perf layer의 2.4배.
  - "perf layer를 키우면 되지 않나?" 라는 질문에 대한 답: GPU 서버 메모리는 보통 1.6–3.2× of GPU memory로 한정.
  - 이게 곧 *eviction이 자주 트리거된다는 뜻*임을 강조.
- **Transition**: eviction이 자주 일어나는 건 알겠는데, 그렇다면 다시 들어올 때 hit rate은 어떨까?

### Slide 10. Observation 2 — `15:00–17:00` (2분)
- **Key message**: KV access의 *temporal locality는 약하다*. 80%의 access가 perf layer 크기를 넘어서고, 어떤 정책도 hit rate ≈ 20%에 머문다.
- **Talk points**
  - *Weighted reuse distance*의 정의 ("두 access 사이에 끼어든 *다른* KV 크기 합")를 천천히. 청중이 이걸 못 잡으면 뒤의 eviction 알고리즘이 무너진다.
  - Figure 6(b) — FIFO, LRU, queue-enhanced 모두 ~20% hit. perf layer가 40.1% KV를 담을 수 있는데도 절반 수준.
  - 왜 약한가? 사용자가 *다음 질문을 생각하는 시간* 동안 다른 사용자 요청이 끼어들기 때문.
- **Transition**: 도착률이 클 뿐 아니라, 도착하는 *각 요청*도 균일하지 않다.

### Slide 11. Observation 3 — `17:00–19:00` (2분)
- **Key message**: KV loading 시간의 *변동계수가 5초 윈도우 안에서도 90% 이상*. 큰 KV 한 개가 작은 KV 행렬을 모두 막는다.
- **Talk points**
  - 두 가지 원인: (a) host DRAM ↔ SSD 대역폭 차, (b) KV size 자체가 수십 MB ~ 수백 MB로 다양 (Figure 8).
  - 결과: head-of-line blocking. FCFS면 큰 capacity-layer KV 1개가 *수백 ms* 동안 GPU를 idle 시킴.
  - 이게 곧 본 논문의 *Mechanism 1*이 풀려는 문제.
- **Transition**: 세 가지 관찰을 종합하면 root cause가 한 줄로 정리된다.

---

## Part 4. Root Cause & Key Idea — 4분

### Slide 12. Root cause — `19:00–21:00` (2분)
- **Key message**: 두 문제 모두 *정보가 한 방향으로만 흐르거나 아예 흐르지 않아서* 발생한다.
- **Talk points**
  - 문제 1: compute가 storage I/O 길이를 모름 → FCFS dispatch가 head-of-line blocking 야기.
  - 문제 2: storage가 사용자 대화 패턴을 모름 → eviction이 자기 측 history만 사용.
  - 두 문제는 본질적으로 *대칭*이다. 두 시스템이 서로 들여다보지 못한다는 한 가지 원인의 두 얼굴.
- **Transition**: 그래서 본 논문의 답은 "두 방향 모두 정보를 흐르게 한다" — bidirectional awareness.

### Slide 13. Key idea — `21:00–23:00` (2분)
- **Key message**: Compute → Storage로는 *답변 길이*를, Storage → Compute로는 *KV 위치/크기*를 흘려보낸다.
- **Talk points**
  - 답변 길이가 왜 의미 있는가? 사람이 답변을 *읽는 시간*을 결정하므로, 그 사이 끼어들 다른 사용자 KV 양을 가늠할 수 있음.
  - KV 위치/크기는 사실 storage 입장에서 자명한 정보. 단지 기존 시스템들이 이걸 compute로 *export*하지 않았을 뿐.
  - 이 두 신호로 두 메커니즘이 만들어진다 — 그게 다음 11장.
- **Transition**: 시스템 그림으로 한 번에 보겠습니다.

---

## Part 5. System Overview — 3분

### Slide 14. 아키텍처 — `23:00–24:30` (1분 30초)
- **Key message**: Bidaw = Scheduler + History Cacher + Eviction Manager. 세 컴포넌트가 두 신호를 주고받는다.
- **Talk points**
  - Figure 9의 ①②③④ 화살표를 따라 시계 방향으로 짚는다.
  - 빨간 점선이 storage 경계 — 이 경계를 넘는 두 신호가 노이즈 없는 핵심.
  - History Cacher(§4)는 Mechanism 3에서 다룬다고 미리 알린다.
- **Transition**: 동작 순서를 더 명확히.

### Slide 15. Workflow — `24:30–26:00` (1분 30초)
- **Key message**: 4단계 — dispatch / inference / answer-length 전달 / threshold 기반 eviction.
- **Talk points**
  - ① Scheduler dispatch는 §3.2.
  - ② History Cacher가 *KV tensor 자체*가 아니라 *storage-efficient tensor*를 잡는다는 게 새로움 (§4).
  - ③ 답변이 끝나는 즉시 길이를 Eviction Manager에게 — *eager*하게 정보 전달.
  - ④ free 공간 5% 미만이면 트리거 → 백그라운드에서 hit potential 계산 후 evict.
- **Transition**: 이제 첫 번째 메커니즘부터 들어갑니다.

---

## Part 6. Mechanism 1 — I/O-aware Scheduling — 7분

### Slide 16. I/O blocking 문제 — `26:00–28:00` (2분)
- **Key message**: GPU iteration(수십 ms) ≪ capacity layer I/O(수백 ms) 이므로 *naive overlap은 의미가 없다*.
- **Talk points**
  - Overlap의 한계: 다음 layer의 KV load와 current layer compute를 겹치는 거리만큼만 가려진다.
  - 그래서 *큐 자체*를 재구성해야 한다는 것이 설계 목표.
  - "큰 KV는 starvation 없이, 작은 KV는 안 막히게" 라는 두 조건을 동시에 만족해야 한다.
- **Transition**: 두 조건을 어떻게 동시에 만족시키는지 보겠습니다.

### Slide 17. Dual queue + disk-HRRN — `28:00–31:00` (3분)
- **Key message**: *Dual queue*가 빠른 I/O와 느린 I/O를 분리하고, *disk-HRRN*이 큰 KV의 starvation을 막는다.
- **Talk points**
  - Ready queue: KV가 perf layer에 있는 요청 — FCFS, GPU 즉시 dispatch.
  - Preparing queue: capacity layer 요청 — 백그라운드 promotion.
  - **disk-HRRN 식**을 칠판처럼 천천히: `R = 1 + waiting / size`.
    - waiting이 크면 큰 KV도 결국 ratio가 올라간다 → starvation 방지.
    - size가 작으면 ratio가 처음부터 높다 → 빠르게 promote.
  - Promotion 시 *원래 도착 시각*을 유지하는 디테일도 강조 — tail latency 폭주 방지.
- **Transition**: 그림으로 보면 더 명확합니다.

### Slide 18. Schedule 예시 — `31:00–33:00` (2분)
- **Key message**: 같은 5개 요청이라도 FCFS는 GPU를 *반쯤 idle*로 두고, I/O-aware는 그 시간을 채운다.
- **Talk points**
  - Figure 11(a): 큰 KV req 1, 2가 머리에서 대기 → 그 뒤 req 3, 4, 5의 perf-layer hit이 같이 막힘.
  - Figure 11(b): req 3, 4, 5 먼저 GPU로. 그 사이 req 2 promote.
  - 결과: 평균 큐잉 시간 5.76s → 2.45s, *57.5% 단축*.
- **Transition**: 이건 compute 측. 이번엔 storage 측 — eviction.

---

## Part 7. Mechanism 2 — Previous-answer-based Eviction — 8분

### Slide 19. Reuse distance ↔ answer length — `33:00–35:00` (2분)
- **Key message**: 이전 라운드 답변이 길수록 다음 KV access의 *weighted reuse distance 하한*이 단조 증가한다 (Spearman ρ = 0.94 ~ 0.98).
- **Talk points**
  - Figure 12 — 12개 시간대 모두에서 같은 패턴. *robustness에 대한 강한 증거*.
  - 직관: 답변이 길면 사용자가 더 오래 읽는다 → 그 사이 다른 사용자 KV가 끼어든다 → reuse distance 커진다.
  - 이건 *human-in-the-loop* 워크로드에 본질적으로 깔린 신호. 다른 도메인으로 일반화 가능성을 잠깐 언급.
- **Transition**: 그러나 reuse distance가 크다고 무조건 evict해도 되는 건 아니다.

### Slide 20. Hit potential — `35:00–37:00` (2분)
- **Key message**: Reuse distance가 *promising 영역*에 있는 access는 LRU에서 hit이 거의 0이지만, *Belady에서는 100%* 가까이 살아 있다.
- **Talk points**
  - Figure 13의 세 영역: small / promising / extreme.
  - Promising 구간이 핵심 — LRU/queue-enhanced의 weakness가 여기에 있다.
  - 따라서 단순한 거리 기반 evict가 아니라, *구간별 hit 확률을 추정*하는 알고리즘이 필요.
- **Transition**: 그 구간별 hit 확률을 어떻게 추정할까?

### Slide 21. Ghost cache + bucketing — `37:00–39:00` (2분)
- **Key message**: Promising 영역을 *m개 fine-grained bucket*으로 자르고, 각 bucket의 hit 확률을 *백그라운드 Belady 시뮬레이션*으로 측정한다.
- **Talk points**
  - 5단계 알고리즘을 그대로 따라간다.
  - *Ghost cache*는 실제 데이터 없이 metadata만 관리 — 그래서 Belady "feasible".
  - 사용자별 과거 분포로 다음 access의 bucket 확률을 추정.
  - *Compute가 넘긴 답변 길이*로 lower bound를 정해 더 작은 bucket의 확률을 0으로 truncate — 이 부분이 bidirectional의 결정적 사용점.
- **Transition**: 마지막으로 결정식.

### Slide 22. Equation 2 — `39:00–41:00` (2분)
- **Key message**: 한 줄짜리 *Overall_potential* 식이 small / promising buckets / extreme의 가중합으로 evict 후보를 결정한다.
- **Talk points**
  - 세 항을 하나씩: *prob_small × 1.0*, *Σ prob_promising(i) × hit_promising(i)*, *prob_extreme × 0.0*.
  - 가장 낮은 potential을 가진 KV가 evict.
  - 비용은 *0.35 ms* — 백그라운드에서 ghost cache가 무거운 일을 다 한다는 점을 강조.
- **Transition**: 이제 마지막 메커니즘 — 어떤 tensor를 캐시할지.

---

## Part 8. Mechanism 3 — Storage-Efficient Tensor — 3분

### Slide 23. Tensor cost efficiency — `41:00–42:30` (1분 30초)
- **Key message**: KV tensor를 캐시하는 건 *최선이 아니다*. 정규화된 activation(tensor 6)이 *cost efficiency 51 GFLOPs/MB*로 KV(30.5)보다 1.67×.
- **Talk points**
  - 새 metric *cost efficiency = saved compute / required space*를 정의.
  - Figure 14(b) — tensor 6에서 곡선이 정점.
  - Tensor 6에서 KV로 돌아가는 변환은 *GPU 1 step* — overhead 작음.
- **Transition**: 그럼 모든 모델에 좋을까? 아니다.

### Slide 24. MHA vs GQA — `42:30–44:00` (1분 30초)
- **Key message**: MHA에서는 tensor 6 캐시가 이득, *GQA에서는 KV tensor 자체가 이미 작아서 다시 KV를 캐시*.
- **Talk points**
  - MHA: head별 K, V 분리 → KV 큼 → tensor 6 우위.
  - GQA: 여러 query head가 K, V 공유 → KV 자체가 작음 → 변환 비용이 우위를 잡아먹음.
  - Llama, Qwen, Bloom, OPT, Baichuan는 MHA — 따라서 본 논문 평가 모델 대부분에서 적용.
- **Transition**: 구현 디테일을 짧게.

---

## Part 9. Implementation — 1분

### Slide 25. 구현 노트 — `44:00–45:00` (1분)
- **Key message**: vLLM 위에 4가지 트릭 — continuous batching, mix-grained PagedAttention, low-priority CUDA stream, inclusive caching.
- **Talk points**
  - **Mix-grained PagedAttention** 디테일은 흥미: history는 256-token 큰 블록, response는 16-token 작은 블록. CPU↔GPU 전송 효율 + 단편화.
  - Storage-efficient tensor → KV 변환은 *low-priority stream*에서 — 본 추론 latency에 영향 없음.
  - Inclusive caching으로 eviction이 *write-free* — 큰 SSD write 트래픽 없음.
- **Transition**: 그래서 평가 결과는?

---

## Part 10. Evaluation — 5분

### Slide 26. Setup — `45:00–46:00` (1분)
- **Key message**: 5개 모델 (OPT 6.7B/13B/30B, Qwen 7B/14B), 자체 trace + ShareGPT, baseline 4종.
- **Talk points**
  - vLLM은 recompute baseline. CachedAttention/FlashGen은 KV-caching SOTA. Optimal은 perf-layer-only ideal.
  - Hardware는 보수적 — 1.5 GB/s SSD. PCIe 4.0이라 GPU 전송은 30 GB/s — *SSD가 진짜 bottleneck*임을 강조.
- **Transition**: 핵심 그림.

### Slide 27. Overall performance — `46:00–47:30` (1분 30초)
- **Key message**: 5개 모델 모두에서 Bidaw가 *Optimal에 거의 붙는다* — 최대 3.58× latency 단축 / 1.83× throughput.
- **Talk points**
  - Figure 15에서 모든 패널의 Bidaw 곡선이 Optimal과 거의 평행.
  - 같은 latency 기준 throughput 비교가 핵심 — *얼마나 더 많은 user/min*을 받을 수 있는가.
  - Bidaw는 *lossless* — 답변 정확도는 FlashGen 등과 동일. 답변 순서만 바뀌므로 LLM 출력 동일.
- **Transition**: 다른 축에서도 보겠습니다.

### Slide 28. Memory sensitivity + miss rate — `47:30–48:30` (1분)
- **Key message**: Host memory가 작을수록 *격차가 더 벌어진다* — 진짜 가치는 메모리 절약 측면.
- **Talk points**
  - Figure 16 — 120GB host에서 Bidaw가 baseline 200GB 수준. 1.75–2.19× user/min.
  - Figure 18 — eviction miss rate가 -57.6% (vs queue-enhanced) / -69.9% (vs FIFO/LRU).
- **Transition**: 마지막으로 tail latency와 내부 분해.

### Slide 29. Tail / Ablation / Overhead — `48:30–50:00` (1분 30초)
- **Key message**: P99 단축, 세 메커니즘이 곱셈으로 기여, overhead는 ms 단위로 무시 가능.
- **Talk points**
  - Tail: P90 −53%, P95 −49%, P99 −47% (vs CachedAttention) — 평균뿐 아니라 *분포의 꼬리*도 잡았다.
  - Ablation: scheduling 1.58×, eviction 1.25×, tensor caching 1.10× — 각 메커니즘이 *독립적으로 의미가 있다*.
  - Overhead: scheduling 0.62 ms, eviction 0.35 ms, KV 변환 < 100 ms — 시스템에 안전하게 추가 가능.
- **Transition**: 마무리.

---

## Part 11. Conclusion & Discussion — 3분

### Slide 30. 정리 / 한계 / 시사점 — `50:00 이후 Q&A 직전` (마지막 3분)
- **Key message**: Bidaw의 진짜 contribution은 "compute와 storage를 양방향으로 들여다보게 한다"는 *원칙*이다. 알고리즘 디테일은 그 원칙을 인스턴스화한 결과.
- **Talk points**
  - **기여**
    - Bidirectional awareness 라는 새로운 설계 원칙.
    - I/O-aware scheduling + previous-answer-based eviction 두 메커니즘.
    - Storage-efficient tensor caching 으로 공간/연산 trade-off 정량화.
    - 5 모델에서 평균 3.58× latency / 1.83× throughput.
  - **한계**
    - 단일 사용자 안에서의 KV 재사용 — *cross-user KV 공유*는 범위 밖 (MeanCache 류와 직교).
    - GQA에서는 storage-efficient tensor 효과가 사라짐.
    - ShareGPT 류 timestamp 부재 trace에선 eviction 효과가 약화 (논문도 인정).
    - 단일 GPU 노드 평가 — disaggregated/multi-node setup은 future work.
  - **시사점**
    - 사람-속도가 storage 정책에 *신호*로 활용 가능하다는 일반적 교훈.
    - HRRN, Belady ghost cache 같은 고전 기법이 LLM 워크로드에서 다시 빛난다.
    - ML serving + storage co-design의 좋은 사례 — 이 영역이 후속 연구로 활발해질 것.
- **Transition**: "여기까지가 Bidaw입니다. 질문 받겠습니다."

---

## 발표 팁 (사전 리허설용)

- **숫자 외울 것**: 3.8× / 2.0× (gap), 22.4 (round), 80% / 20% (locality), 51 vs 30.5 (cost eff), 3.58× / 1.83× (final).
- **잘못 쓰기 쉬운 용어**: *weighted* reuse distance — 그냥 reuse distance가 아니라 *byte 합*. 이걸 일찍 정의해두지 않으면 §3.3 전체가 흔들린다.
- **놓치기 쉬운 디테일**:
  - HRRN의 변형이 disk-HRRN — *I/O 시간 ≈ KV size* 라는 가정이 들어 있음.
  - Inclusive caching이 큰 write trafic을 막는다는 점 — eviction 비용이 거의 0이 되는 이유.
- **질문 대비**:
  - "GQA에서는?" → tensor caching 비활성, 나머지 두 메커니즘은 그대로 적용.
  - "왜 답변 길이가 신호로 충분한가?" → 사용자가 답을 다 읽고 다음 질문을 만들기까지 *최소 시간 하한*을 만든다.
  - "ShareGPT에서 효과 약화" → timestamp 시뮬레이션이 Poisson이라 답변 길이와 doubt 시간이 분리되기 때문.
  - "Bidaw가 lossless인가?" → 답변 정확도 그대로. 단지 *user 1*과 *user 2*의 처리 *순서*가 바뀔 뿐. LLM 출력은 동일.
