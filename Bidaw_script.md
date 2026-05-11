# Bidaw 세미나 발표 스크립트 (50분 · 발화 원고)

논문: **Bidaw: Enhancing Key-Value Caching for Interactive LLM Serving via Bidirectional Computation–Storage Awareness** — Hu et al., FAST '26

> 사용 방법
> - 각 슬라이드 블록은 (1) 핵심 메시지, (2) **발표 멘트** — 실제 청중 앞에서 말할 문장, (3) 보조 노트, (4) 이어가기로 구성된다.
> - 발표 멘트는 한 문장씩 끊어 읽기 좋게 다듬었다. 굳이 그대로 읽지 않아도 되지만, 문장의 *호흡 단위*는 그대로 가져가면 시간이 맞는다.
> - 보조 노트는 청중 반응에 따라 추가로 던질 수 있는 정보다.
> - 시간 박스 `[X:XX–X:XX]`는 슬라이드별 분량.

---

## Part 1. Opening — 3분

### Slide 1. Title — `0:00–0:30` (30초)

- **핵심 메시지**: 오늘 다룰 논문은 FAST '26의 *Bidaw* — KV 캐싱에서 compute와 storage가 서로의 정보를 들여다보게 만드는 시스템.
- **발표 멘트**
  > "안녕하세요. 오늘은 FAST '26에 발표된 *Bidaw* 라는 논문을 같이 보겠습니다. Tsinghua와 China Telecom이 공동으로 작업한 논문이고, 인터랙티브 LLM 서빙에서 KV 캐시를 어떻게 관리할지에 대한 시스템입니다. 한 마디로 요약하면, *compute*와 *storage*가 서로의 정보를 들여다보게 만든다는 단순한 원칙으로 큰 격차를 메운 논문입니다."
- **보조 노트**
  - Tsinghua 단독이 아니라 China Telecom 공동임을 강조하면 트레이스의 신빙성이 자연스럽게 따라온다.
  - 핵심 키워드 두 개를 미리 청중 머릿속에 심기: *interactive LLM serving*, *bidirectional awareness*.
- **이어가기**: "50분 동안 무엇을 다룰지, 먼저 길을 깔겠습니다."

---

### Slide 2. Agenda — `0:30–3:00` (2분 30초)

- **핵심 메시지**: 세 가지 메커니즘과 평가 한 묶음. 셋이 별개의 기여이고, 평가는 5개 모델 위에서 폭넓게 검증.
- **발표 멘트**
  > "발표는 크게 여덟 단계로 나뉩니다. 우선 인터랙티브 LLM 서빙이라는 워크로드가 정확히 무엇인지 *Background*에서 합을 맞추고, 곧 *Motivation*에서 KV 로딩이 왜 병목이 되는지 세 가지 관찰을 통해 보여드립니다.
  >
  > 그다음 이 논문이 제안하는 *Key Idea*, 그러니까 *bidirectional awareness*를 짧게 던지고, 이어서 그 원칙을 구체화한 *세 가지 메커니즘*을 차례로 다룹니다. *Mechanism 1*은 compute 측의 스케줄링, *Mechanism 2*는 storage 측의 eviction, *Mechanism 3*은 어떤 텐서를 캐싱할지에 대한 트레이드오프입니다.
  >
  > 마지막으로 *Evaluation*에서 핵심 plot 일곱 개 정도를 빠르게 훑고, *Discussion*에서 한계와 일반화 가능성까지 짚겠습니다. 이 마지막 부분은 제가 *반드시* 짚고 가겠다는 약속을 미리 드립니다."
- **보조 노트**
  - 청중이 시스템 전공인지 ML 전공인지에 따라 비중 조절. 시스템 청중이면 Mechanism 1, 2를 좀 더 빠르게.
- **이어가기**: "그러면 첫 번째 — 인터랙티브 LLM 서빙이라는 워크로드가 무엇인지부터."

---

## Part 2. Background — 8분

### Slide 3. Interactive LLM serving — `3:00–4:30` (1분 30초)

- **핵심 메시지**: 사용자 한 명이 *수십 번* 라운드를 주고받는다는 사실 하나가 이 논문의 모든 설계 결정의 출발점.
- **발표 멘트**
  > "인터랙티브 LLM 서빙은 한 마디로 사용자와 LLM이 *번갈아 가며 여러 라운드를 주고받는* 환경입니다. Replika 같은 가상 동반자, Duolingo Max 같은 학습 보조, 그리고 고객 응대 챗봇이 대표적인 예시입니다.
  >
  > 이 논문이 쓴 트레이스에서는 — 그림 오른쪽에 슬쩍 보이지만 — 사용자 한 명당 평균 22.4 라운드를 주고받습니다. P90이 45 라운드까지 갑니다. 흔히 쓰이는 ShareGPT 트레이스가 평균 5.7 라운드인 것과 비교하면 *4배 이상* 깁니다.
  >
  > 그리고 가장 중요한 점 — Figure 1이 보여주는 것처럼, 라운드 N의 답변을 만들 때 0번부터 N-1번 라운드까지의 *모든* KV 텐서가 attention 입력으로 다시 들어갑니다. 즉 KV가 누적되면서 살아 있어야 한다는 뜻이고, 이것이 이 논문의 모든 설계가 시작되는 지점입니다."
- **보조 노트**
  - "22.4"는 키 숫자다. 이 발표 내내 두세 번 반복해 자주 들리게 한다.
  - "재계산을 피해야 한다"는 다음 슬라이드 KV cache로 매끄럽게 연결된다.
- **이어가기**: "그러면 이 KV가 정확히 무엇이고, 왜 캐싱해야 하는지 잠깐 합을 맞춥시다."

---

### Slide 4. KV cache의 역할 — `4:30–6:30` (2분)

- **핵심 메시지**: KV cache는 attention 재계산을 피하는 *유일한* 수단이고, 그 크기는 토큰 수에 비례해 늘어남.
- **발표 멘트**
  > "self-attention 식 한 줄로 핵심을 짚자면 — `softmax(Q·Kᵀ/√d)·V`입니다. 추론 단계에서 새 토큰 하나를 만들 때, *새 토큰의 Q*만 새로 계산하면 됩니다. 과거 토큰들의 K와 V는 그대로 유지되므로, 그걸 저장해두면 *재사용*만 하면 됩니다. 이게 바로 KV cache입니다.
  >
  > 재사용해도 *수학적으로 완전히 동일한* 결과가 나옵니다. 그래서 정확도 손실 없이 연산을 줄일 수 있는, 사실상 *유일한* 방법입니다. 다만 비용이 있죠 — 토큰 수에 비례해서 KV 크기가 선형으로 늘어납니다. 식으로 쓰면 *KV size = 2 · t · L · h · d · dtype 크기*입니다.
  >
  > 구체적인 숫자 하나만 외워두시면 좋습니다. OPT-13B 모델에서 2,048 토큰 history면 사용자당 약 *0.78 GB*. 이 값이 나중에 perf layer 200 GB 논의와 그대로 이어지니까, 기억해두시면 다음 슬라이드 흐름이 쉽습니다.
  >
  > 마지막으로 한 가지 — 이 논문이 다루는 KV는 *한 사용자의 여러 라운드 대화* 안에서의 재사용입니다. 사용자 *간* KV 공유는 범위 밖이고, 그건 MeanCache 류의 다른 줄기 연구입니다."
- **보조 노트**
  - 식을 칠판처럼 천천히 짚는다. 그러나 청중이 ML 전공자가 많으면 빠르게 흘려도 된다.
  - "0.78 GB / user" 숫자는 이후 Observation 1에서 480 GB로 부풀어오를 때 다시 호출하면 임팩트 있다.
- **이어가기**: "그러면 이 KV가 GPU에 다 들어가느냐 — 안 들어갑니다. 그게 이 논문의 출발선이죠."

---

### Slide 5. 왜 GPU 메모리에 다 담을 수 없는가 — `6:30–8:00` (1분 30초)

- **핵심 메시지**: 사용자가 30명/분만 도착해도 동시 캐싱 KV가 perf layer(host memory)도 *3.91배* 초과.
- **발표 멘트**
  > "왜 GPU에 다 못 두느냐 — 단순한 산수입니다. A800 80 GB 한 장에 모델 weight와 activation을 올리고 나면, KV가 들어갈 자리가 그렇게 많지 않습니다. 그래서 자연스럽게 host memory를 *perf layer*로 쓰게 됩니다. 그런데 호스트 메모리도 무한하지 않죠 — 일반적인 LLM 서버 구성에서 host memory는 GPU memory의 1.6에서 3.2배 정도입니다. 곱해 봐도 200에서 250 GB 정도가 한계입니다.
  >
  > 그런데 Figure 5의 빨간 수평선이 바로 그 200 GB 한계입니다. 가로축이 분당 도착 사용자 수인데, *10 users/min만 넘어도* OPT-13B에서 캐싱돼야 할 KV 양이 이미 그 선을 넘습니다. 30 users/min쯤 되면 약 480 GB까지 부풀어오릅니다.
  >
  > 슬라이드 왼쪽 아래의 박스가 이를 한 줄로 요약합니다 — 동시 캐싱 KV가 perf layer를 *최대 3.91배* 초과합니다. 따라서 SSD까지 동원하는 2-tier 캐싱은 *선택이 아니라 필연*이 됩니다."
- **보조 노트**
  - "3.91배"라는 수치는 OPT-13B에 한정. OPT-6B는 좀 더 작다는 점을 청중이 물으면 답할 준비.
  - 200 GB 수평선은 다음 슬라이드에서도 등장하므로 여기서 강조해두면 좋다.
- **이어가기**: "그래서 기존 솔루션이 어떻게 생겼는지 잠깐 보고 가겠습니다."

---

### Slide 6. Two-tier storage — `8:00–9:30` (1분 30초)

- **핵심 메시지**: 직전 SOTA인 CachedAttention과 FlashGen은 *write*를 critical path에서 빼냈지만, *read*는 여전히 critical path 위에 남아 있음.
- **발표 멘트**
  > "기존 2-tier 캐싱은 그림처럼 perf layer는 host DRAM, capacity layer는 SSD로 나누는 구조입니다. 직전 SOTA가 두 시스템이 있습니다 — CachedAttention(ATC '24)과 FlashGen(FAST '25). HCache라는 EuroSys '25 논문도 비슷한 방향입니다. 이번 발표의 Bidaw는 이 둘을 직접적인 베이스라인으로 삼습니다.
  >
  > 핵심은 *어디가 critical path에 남아 있느냐*입니다. 쓰기, 그러니까 KV를 capacity layer로 evict 하는 작업은 백그라운드로 빠졌습니다. 그래서 쓰기는 더 이상 문제가 아닙니다. 그런데 *읽기*는, GPU가 inference 직전에 반드시 perf layer에서 KV를 끌어와야 하므로 *여전히 critical path 위에 남아 있습니다*.
  >
  > 이 논문이 정확히 겨냥하는 지점이 바로 여기 — *load 경로의 비효율*입니다."
- **보조 노트**
  - CachedAttention과 FlashGen이 어떤 시스템인지 청중이 모르면 한 문장씩 더 풀어준다. ATC '24의 *queue-enhanced LRU*, FAST '25의 *inclusive caching*.
  - HCache는 intermediate activation 캐싱이라 Mechanism 3 슬라이드의 친척이다 — 거기서 다시 짚을 거라고 예고해두면 흐름이 깔끔하다.
- **이어가기**: "그 비효율이 얼마나 큰지 숫자로 확인하겠습니다."

---

### Slide 7. KV loading이 곧 critical path — `9:30–11:00` (1분 30초)

- **핵심 메시지**: 모든 KV가 perf layer에 있다고 *가정한* ideal과 비교하면 latency *3.8배*, throughput *2배* 격차.
- **발표 멘트**
  > "Figure 3은 이 격차를 한 그림으로 보여줍니다. 빨간 화살표로 'Gap'이라고 표시된 두 군데가 핵심입니다. 가로축이 분당 사용자 수, 세로축이 평균 latency입니다. 위에서부터 — KV recomputing은 매번 다시 계산하는 vLLM 베이스라인이고, 그 아래가 CachedAttention과 FlashGen 곡선, 가장 아래의 갈색 마름모가 *ideal* — 모든 KV가 perf layer에 있다고 가정한 상한선입니다.
  >
  > 같은 사용자 도착률에서 — ideal과 비교했을 때, 기존 시스템들은 응답 latency가 *최대 3.8배* 더 큽니다. 같은 latency 기준으로 throughput을 비교하면 *최대 2배* 적습니다. 이 격차가 이 논문이 정확히 메우려는 것입니다.
  >
  > 환경 조건을 못 박아두면 — OPT-13B 모델, A800 80 GB, host 200 GB, SSD 1.5 GB/s입니다. 이 숫자들은 평가 슬라이드에서도 그대로 나오니까 청중 머릿속에 한 번 박아두면 좋습니다."
- **보조 노트**
  - "Gap"이 두 군데 표시된 이유 — 두 베이스라인 모두와의 차이를 동시에 보여주려는 의도다.
  - "그런데 왜 ideal과 격차가 생기는가?"라는 청중의 자연스러운 질문이 다음 motivation 섹션으로 이어지게 한다.
- **이어가기**: "그 격차의 *근본 원인*을 찾기 위해, 실서비스 트레이스로 워크로드를 직접 들여다보겠습니다."

---

## Part 3. Motivation — 8분

### Slide 8. 워크로드 소개 — `11:00–13:00` (2분)

- **핵심 메시지**: 이 논문이 쓴 워크로드는 *기존 공개 트레이스에는 없는* 형태 — 사용자 단위 timestamp가 보존된 100만+ 라운드 트레이스.
- **발표 멘트**
  > "이 논문이 쓴 트레이스가 어떤 것인지부터 잠깐 짚겠습니다. China Telecom의 omni-channel 운영센터에서 받은, *100만+ 라운드 분량의 실서비스* 대화 트레이스입니다. 가장 중요한 점은 *사용자 단위 timestamp*가 보존되어 있다는 거예요. 그래야 사용자가 한 답변을 받고 *언제 다음 질문을 던졌는지*를 측정할 수 있고, 이게 뒤에 나올 핵심 신호가 됩니다.
  >
  > 기존 공개 트레이스와 비교하면 — ShareGPT는 한 사용자당 평균 5.7 라운드로 *너무 짧고*, Mooncake는 query 길이가 12k 토큰 이상으로 길지만 *대화 패턴 자체가 없습니다*. 이 논문의 트레이스만 — 22.4 라운드에 한 답변이 평균 36 토큰 — *인터랙티브 워크로드의 정의에 가장 잘 맞습니다*.
  >
  > 그래서 이 트레이스 위에서만 보이는 세 가지 관찰을, 이어지는 슬라이드 세 장에서 차례대로 보여드리겠습니다."
- **보조 노트**
  - "사용자 단위 timestamp 보존"이라는 점을 강조해두지 않으면, ShareGPT의 결과가 약한 이유(Slide 28)를 나중에 설명하기 어렵다.
  - 청중이 "이 트레이스 공개되나?"라고 묻는다 — GitHub `ShipengHu-777/Interactive-conversation-workload`에 공개되어 있다고 답.
- **이어가기**: "그러면 첫 번째 관찰 — 동시에 캐싱되어 있어야 할 KV의 총량부터."

---

### Slide 9. Observation 1 — `13:00–15:00` (2분)

- **핵심 메시지**: 한 사용자의 KV가 22.4 라운드 동안 살아있어야 하니, 도착률이 오르면 동시 KV 총량이 *perf layer를 그대로 넘어버린다*.
- **발표 멘트**
  > "Figure 5의 그림을 잘 보시면 — 가로축이 분당 도착 사용자 수, 왼쪽 세로축이 동시에 캐싱돼야 할 *KV 총량*, 오른쪽 세로축이 *동시 사용자 수*입니다. 파란 삼각형이 OPT-13B, 초록 삼각형이 OPT-6B입니다.
  >
  > 핵심은 — 한 사용자의 KV가 평균 22.4 라운드 동안 *살아 있어야 한다*는 사실입니다. 사용자는 답변을 읽고, 생각하고, 다음 질문을 던지죠. 그 사이 KV는 evict 될 수 없습니다. 그래서 도착률이 올라가면 동시 KV 총량이 *선형으로* 증가합니다. OPT-13B 기준으로 30 users/min에서 약 480 GB까지 부풀어오릅니다.
  >
  > 빨간 수평선이 perf layer 200 GB입니다. 이미 *10 users/min에서부터* 넘어서고, 30 users/min에서는 *2.4배*까지 넘습니다. 그러면 자연스러운 반응이 — "perf layer를 키우면 되지 않나요?" 입니다. 그런데 host memory는 보통 GPU memory의 1.6에서 3.2배로 묶여 있어서, 마음대로 키우기 어렵습니다.
  >
  > 결국 *eviction이 매우 자주 트리거된다*는 뜻입니다. eviction 정책이 시스템 성능을 좌우하게 됩니다."
- **보조 노트**
  - "왜 perf layer를 키우면 안 되나요?"는 단골 질문 — host 메모리는 보통 GPU 메모리의 1.6~3.2배 범위에 묶여 있다고 답.
  - 30 users/min은 OPT-13B 기준이고, OPT-6B는 좀 더 여유가 있다는 점도 알아둔다.
- **이어가기**: "eviction이 자주 일어나는 건 알겠는데, 다시 들어올 때 hit rate는 어떨까요?"

---

### Slide 10. Observation 2 — `15:00–17:00` (2분)

- **핵심 메시지**: KV access의 *temporal locality가 약하다*. 80%의 access가 perf layer 크기를 넘어서고, 어떤 정책도 hit rate가 20% 수준에 머무름.
- **발표 멘트**
  > "두 번째 관찰의 핵심 도구는 *weighted reuse distance*라는 개념입니다. 한 KV가 두 번 access 되는 사이에, *다른 KV들이 byte 단위로 얼마나 끼어들었는지*를 더한 값이에요. 횟수가 아니라 byte 합이라는 점이 중요합니다. 그래야 perf layer 크기와 직접 비교가 됩니다.
  >
  > Figure 6의 왼쪽 — CDF를 보시면 가로축이 weighted reuse distance, 세로축이 누적 비율입니다. *80%의 access가 200 GB를 넘습니다*. 즉, 다시 access 될 때까지 perf layer를 한 번씩 다 갈아치울 만큼 다른 KV가 끼어듭니다.
  >
  > 오른쪽 막대그래프가 더 결정적입니다. FIFO, LRU, queue-enhanced — CachedAttention이 쓰는 그 정책까지 — 모두 hit rate가 *20% 수준*에 머뭅니다. perf layer가 평균적으로 KV의 40.1%를 담을 수 있는데도 hit는 그 절반 정도라는 게 어색하죠.
  >
  > 왜 약한가요? 사용자가 답변을 *읽고 생각하는 시간* 동안, 다른 사용자들의 요청이 끊임없이 끼어들기 때문입니다. 이건 인터랙티브 워크로드에 *본질적으로 깔린* 성질이고, 그래서 LRU 류의 정책으로는 잡기 어렵습니다."
- **보조 노트**
  - *Weighted reuse distance* 정의는 이 발표의 가장 큰 기술적 부담 — 여기서 청중을 잃으면 §3.3 전체가 흔들린다. 한 번 더 풀어서라도 확실히.
  - "Belady라면 어떤가요?"는 다음 슬라이드 미리보기 — 다음 두 슬라이드에서 다룬다고 알린다.
- **이어가기**: "도착률이 클 뿐 아니라, 도착하는 *각 요청*도 균일하지 않다는 게 세 번째 관찰입니다."

---

### Slide 11. Observation 3 — `17:00–19:00` (2분)

- **핵심 메시지**: KV loading 시간의 *변동계수가 5초 윈도우 안에서도 90% 초과*. 큰 KV 하나가 뒤따르는 작은 KV들까지 막아버림.
- **발표 멘트**
  > "세 번째 관찰은 *KV loading 시간의 변동성*입니다. Figure 7이 시간 윈도우 별로 변동계수 — coefficient of variation — 를 측정한 건데요, 가로축이 윈도우 크기(5초부터 640초까지), 세로축이 변동계수입니다. *어느 시간 척도에서 봐도 90%를 넘습니다*. 5초 윈도우에서도 그대로 90% 이상이라는 게 충격적이에요.
  >
  > 원인은 두 가지입니다. 첫째, host DRAM과 SSD의 대역폭이 *수십 배 차이*입니다. 둘째, Figure 8을 보시면 — 요청마다 로딩되는 KV size 자체가 *수십 MB부터 수백 MB까지* 매우 다양합니다. 이 두 가지가 곱해지면 loading 시간이 균일할 수가 없습니다.
  >
  > 함의가 뭐냐 — *head-of-line blocking*입니다. FCFS로 dispatch 하면, 큰 capacity-layer KV 하나가 큐 머리에 박힐 때 *수백 ms 동안* GPU가 그 KV가 끝나기를 기다립니다. 그동안 뒤에 있는, 빨리 처리 가능한 perf-layer hit 요청까지 같이 막혀버립니다. 이게 곧 *Mechanism 1*이 풀려는 정확한 문제입니다."
- **보조 노트**
  - "왜 prefetch나 overlap으로 못 가리나요?"는 Slide 16에서 정식으로 다룬다 — 여기서는 슬쩍만 예고.
  - 변동계수 90%는 일반적으로 "매우 큰 분산"의 기준선. 청중이 이 의미를 모르면 한 줄 추가 설명.
- **이어가기**: "세 가지 관찰을 종합하면 root cause가 한 줄로 정리됩니다."

---

## Part 4. Root Cause & Key Idea — 4분

### Slide 12. Root cause — `19:00–21:00` (2분)

- **핵심 메시지**: 두 문제 모두 *compute와 storage 사이에서 정보가 한쪽으로만 흐르거나 아예 끊겨 있어서* 생긴다.
- **발표 멘트**
  > "세 관찰을 종합하면 두 문제로 정리됩니다. 슬라이드 위쪽 박스 두 개를 보시면 — 첫 번째 문제는 *compute가 storage I/O 시간을 모른다*는 점입니다. 어떤 요청의 KV가 perf layer에 있는지 capacity layer에 있는지, 크기가 얼마인지 — compute는 깜깜합니다. 그래서 그냥 FCFS로 dispatch 하고, 큰 I/O 하나가 큐 머리에 박히면 GPU가 idle 상태가 됩니다.
  >
  > 두 번째 문제는 *storage가 사용자 대화 패턴을 모른다*는 점입니다. eviction은 자기 측의 KV access history만 보고 결정합니다. 그런데 그 history는 약한 temporal locality 때문에 정확한 신호가 아닙니다. 결과적으로 hit rate가 20% 수준에 머뭅니다.
  >
  > 슬라이드 아래쪽 박스가 이 두 문제를 한 줄로 묶습니다 — *정보가 한쪽 방향으로만 흐르거나, 아예 흐르지 않는다*. 두 문제는 사실 *대칭*이에요. 두 시스템이 서로를 못 본다는 *하나의* 원인이 두 가지 증상으로 드러난 겁니다.
  >
  > 그래서 Bidaw의 가설은 단순합니다 — *두 방향 모두 정보를 흐르게 하면 두 문제가 모두 해결된다*."
- **보조 노트**
  - 이 슬라이드가 발표 전체의 "축" — 청중이 여기서 핵심 아이디어를 잡으면 나머지가 매끄럽게 따라온다.
  - "대칭"이라는 표현이 효과적이다. 청중이 둘을 별개 문제로 보면 메시지가 약해진다.
- **이어가기**: "그래서 이 논문의 답은 *양방향으로 정보를 흐르게 한다* — bidirectional awareness 입니다."

---

### Slide 13. Key idea — `21:00–23:00` (2분)

- **핵심 메시지**: Compute → Storage로는 *답변 길이*를, Storage → Compute로는 *KV 위치와 크기*를 흘려보낸다.
- **발표 멘트**
  > "양방향이라고 했으니, 두 방향이 각각 어떤 신호를 흘리는지 보겠습니다.
  >
  > 왼쪽 박스 — *Compute → Storage* 방향입니다. compute가 storage에게 보내는 신호는 *이전 라운드의 모델 답변 길이*입니다. 단순해 보이지만, 이게 왜 의미가 있냐 — 답변이 길수록 사용자가 *읽는 시간*이 길어집니다. 그 사이에 다른 사용자들의 요청이 끼어들 양을 예측할 수 있고, 그게 곧 다음 KV access의 *weighted reuse distance 하한*이 됩니다. storage는 이 신호를 받아서 *어떤 KV가 다음에 다시 hit 될 가능성이 낮은가*를 추정하고, 그 KV부터 evict 합니다.
  >
  > 오른쪽 박스 — *Storage → Compute* 방향입니다. storage가 compute에게 보내는 신호는 *각 요청 KV의 위치와 크기*입니다. 사실 이건 storage 입장에서 자명한 정보예요 — 어느 KV가 어느 tier에 있는지, 크기가 얼마인지 storage는 이미 알고 있습니다. 다만 *기존 시스템들이 그 정보를 compute로 내보내지 않았을 뿐*입니다. compute는 이 정보를 받아서 두 개의 큐 — ready와 preparing — 로 요청을 갈라놓고, GPU가 idle 되지 않게 스케줄링합니다.
  >
  > 이 두 신호에서 두 가지 메커니즘이 자연스럽게 나옵니다. 이게 다음 11장의 큰 줄거리입니다."
- **보조 노트**
  - "답변 길이가 어떻게 신호가 되는가" — 이게 직관적으로 이해돼야 청중이 §3.3을 따라온다. 사람의 *읽는 시간*이라는 비유로 강조.
  - "기존 시스템들이 내보내지 않았을 뿐"이라는 표현이 — 단순한 정보의 *흐름*이 만드는 큰 차이를 강조한다.
- **이어가기**: "시스템 그림으로 한눈에 보겠습니다."

---

## Part 5. System Overview — 3분

### Slide 14. 시스템 아키텍처 — `23:00–24:30` (1분 30초)

- **핵심 메시지**: Bidaw = Scheduler + History Cacher + Eviction Manager. 세 컴포넌트가 두 신호를 주고받는다.
- **발표 멘트**
  > "Figure 9를 시계 방향으로 따라가겠습니다. 가운데 빨간 점선이 *compute*와 *two-tier storage*를 가르는 경계입니다. 이 경계를 *양방향으로* 넘는 두 신호가 이 논문의 핵심 발명입니다.
  >
  > 위쪽 — *compute engine*에 세 가지가 있습니다. 첫째, *Scheduler* (§3.2) — storage로부터 KV 위치와 크기를 받아서 *ready queue*와 *preparing queue*로 나눕니다. 둘째, *History Cacher* (§4) — GPU 추론 중 생성되는 *intermediate tensor*들 중에서 *공간 대비 연산 절약이 최대*인 텐서, 즉 *storage-efficient tensor*만 골라서 storage로 보냅니다. 이 부분은 Mechanism 3에서 다시 다룹니다.
  >
  > 아래쪽 — *two-tier storage*입니다. *Eviction Manager* (§3.3)가 핵심이에요. compute에서 답변 길이 신호를 받아서, 다음 KV access의 reuse distance 하한을 추정하고, *hit potential이 가장 낮은* KV를 capacity layer로 evict 합니다.
  >
  > 정리하면 — 위에서 아래로 *future access timing*이 흐르고, 아래에서 위로 *KV location & size*가 흐릅니다. *Bidirectionally aware*라는 문구가 그 양방향성을 가리킵니다."
- **보조 노트**
  - 시계 방향이라는 동선이 중요하다 — 청중의 눈이 무작위로 헤매면 그림의 의미가 사라진다.
  - "intermediate tensor"라는 용어가 처음 등장하는 슬라이드. 여기서 너무 깊이 들어가지 말고 Mechanism 3에서 다룬다고 예고만.
- **이어가기**: "동작 순서를 좀 더 명확히 보겠습니다."

---

### Slide 15. Workflow — `24:30–26:00` (1분 30초)

- **핵심 메시지**: 4단계 — dispatch → inference → answer length 전달 → threshold 기반 eviction.
- **발표 멘트**
  > "전체 동작을 네 단계로 정리하면 — ① 사용자 요청이 도착하면 Scheduler가 KV 위치와 크기를 storage에서 조회해 ready queue 또는 preparing queue로 보냅니다. ② GPU가 inference를 진행하면서 동시에 생성되는 storage-efficient tensor를 History Cacher가 저장합니다. KV tensor 자체가 아니라 *더 작은 intermediate tensor*를 저장한다는 점이 새롭습니다 — MHA 모델 한정입니다.
  >
  > ③ GPU 응답이 끝나는 순간, 그 답변의 토큰 길이를 *바로* Eviction Manager에게 전달합니다. 이게 위에서 아래로 흐르는 신호고요. Eviction Manager는 이 신호로 다음 KV access의 reuse distance 분포를 추정합니다.
  >
  > ④ perf layer의 여유 공간이 5% 미만이 되면 eviction을 트리거합니다. 백그라운드에서 hit potential을 계산하고, 가장 낮은 KV를 capacity layer로 옮깁니다. 옮기는 게 아니라 사실 *복사본이 capacity layer에 이미 있으므로* perf layer에서 포인터만 제거하면 됩니다 — *inclusive caching*이라는 트릭입니다.
  >
  > 그러면 이제 첫 번째 메커니즘부터 자세히 들어갑니다."
- **보조 노트**
  - "inclusive caching"이 여기서 처음 등장 — Mechanism 3과 구현 노트에서 더 다루지만, 여기서 한 번 짚어두면 좋다.
  - "5% threshold"는 hyperparameter — 논문이 sensitivity 분석을 안 했다는 점은 Q&A 대비.
- **이어가기**: "첫 번째 메커니즘은 compute 측의 스케줄링부터."

---

## Part 6. Mechanism 1 — I/O-aware Scheduling — 7분

### Slide 16. I/O blocking 문제 — `26:00–28:00` (2분)

- **핵심 메시지**: GPU iteration이 수십 ms, capacity-layer I/O가 수백 ms — 차이가 너무 커서 *단순 overlap만으로는 부족*.
- **발표 멘트**
  > "Mechanism 1을 시작하기 전에, 자연스러운 질문 하나 — '왜 그냥 prefetch나 overlap으로 가릴 수 없는가?' 입니다.
  >
  > 답은 시간 척도가 너무 다르기 때문입니다. GPU의 한 iteration, 즉 다음 토큰 하나를 만드는 시간은 *수십 ms*입니다. 그런데 capacity layer SSD에서 KV 하나를 읽어오는 시간은 *수백 ms*입니다. 10배 이상 차이가 납니다. 다음 layer의 KV load와 현재 layer compute를 겹쳐도, 가려지는 건 *수십 ms*뿐입니다. 나머지 수백 ms 동안 GPU는 계속 idle 상태입니다.
  >
  > naive overlap이 의미가 없다는 뜻이에요. 그래서 이 논문의 접근은 — *큐 자체를 재구성한다*는 겁니다.
  >
  > 슬라이드 아래쪽 회색 박스가 설계 목표입니다 — *느린 I/O 요청이 빠른 I/O 요청을 막지 않게 하면서, 큰 KV 요청도 starvation 없이 진행시킨다*. 두 조건을 *동시에* 만족해야 합니다. 작은 KV만 우대하면 큰 KV가 영원히 못 들어가니까요."
- **보조 노트**
  - "왜 더 짧은 iteration이 안 되나" 같은 추가 질문 — model size와 batch size 곱으로 결정되는 *근본 시간*이라 단축이 어렵다.
- **이어가기**: "두 조건을 어떻게 함께 맞추는지, 다음 슬라이드에서 정확한 알고리즘으로."

---

### Slide 17. Dual queue + disk-HRRN — `28:00–31:00` (3분)

- **핵심 메시지**: *Dual queue*가 빠른 I/O와 느린 I/O를 갈라놓고, *disk-HRRN*이 큰 KV의 starvation을 막는다.
- **발표 멘트**
  > "두 가지 기법이 같이 갑니다.
  >
  > 첫째, *Dual queue*입니다. 왼쪽 박스가 그 정의를 풀어줍니다. *Ready queue*에는 KV가 perf layer에 있는 요청만 들어갑니다. 빨리 처리되니까 FCFS로 GPU에 바로 보냅니다. *Preparing queue*는 KV가 capacity layer에 있는 요청들이에요 — 백그라운드로 perf layer로 끌어올린 다음, ready queue로 *promote* 시킵니다.
  >
  > 이렇게 갈라놓으면 빠른 요청이 느린 요청 뒤에 줄 서지 않습니다. 그런데 한 가지 디테일이 중요한데 — promotion 이후 ready queue 안에서의 위치는 *원래 도착 시각*으로 결정합니다. promote 된 시점이 아니에요. 이게 없으면 promote 늦은 요청은 영원히 뒤로 밀려서 *tail latency가 폭주*합니다.
  >
  > 둘째, *disk-HRRN*입니다. 오른쪽 박스의 식 — `R = 1 + waiting time / KV size`. 이게 preparing queue 안에서 어떤 요청부터 promote 할지 결정하는 우선순위입니다. 고전 운영체제의 HRRN을 변형한 거예요 — service time 대신 KV size를 넣었습니다. *I/O 시간이 KV size에 비례한다*는 가정이 깔려 있죠.
  >
  > 효과는 두 가지입니다. *작은 KV*는 처음부터 ratio가 높으니까 빨리 promote 됩니다. *큰 KV*는 ratio가 낮지만, waiting 시간이 길어지면 결국 따라잡혀 promote 됩니다 — *starvation을 방지*하는 자동 메커니즘입니다."
- **보조 노트**
  - HRRN의 origin (Brinch Hansen, 1971)을 한 줄로 짚으면 청중이 reuse 신호로 받아들인다.
  - "왜 service time 대신 KV size?" — I/O 시간 ≈ KV size / SSD bandwidth 라는 단순 가정. 청중이 더 깊이 물으면 답변.
- **이어가기**: "그림으로 보면 차이가 더 명확합니다."

---

### Slide 18. 동작 예시 — `31:00–33:00` (2분)

- **핵심 메시지**: 같은 5개 요청이라도 FCFS는 GPU를 *반쯤 놀게* 두지만, I/O-aware는 그 시간을 채운다.
- **발표 멘트**
  > "Figure 11을 위아래로 비교하면서 보시면 됩니다. 위가 (a) FCFS, 아래가 (b) I/O-aware scheduling. 같은 요청 5개, 같은 도착 순서입니다. req 1과 req 2의 KV는 capacity layer에 있고 큽니다. req 3, 4, 5의 KV는 perf layer에 있고 작습니다.
  >
  > (a) FCFS — 큰 KV인 req 1이 큐 머리에 박힙니다. 그동안 GPU와 perf-layer I/O가 둘 다 idle 상태가 됩니다. 뒤에 있는 req 3, 4, 5가 처리될 수 있는데도 — 큐 순서를 못 깨니까 그냥 기다립니다.
  >
  > (b) I/O-aware — req 3, 4, 5가 ready queue에 들어가 있으니까 *먼저 GPU로 보냅니다*. 그 사이에 req 2가 promote 되어 ready queue로 옮겨갑니다. req 1은 가장 큰 거니까 disk-HRRN ratio가 낮지만, 결국 waiting이 누적되면서 promote 됩니다.
  >
  > 결과 — 평균 큐잉 시간이 *5.76초에서 2.45초로 57.5% 단축*됩니다. Mechanism 1 단독의 효과로 throughput이 1.58배 향상되는 것을 ablation에서 확인할 수 있습니다."
- **보조 노트**
  - "큰 KV가 영원히 못 들어가는 케이스는 없나요?" — disk-HRRN의 waiting 누적으로 결국 promote 된다.
  - 57.5%, 1.58배는 외워두자.
- **이어가기**: "여기까지가 compute 측. 다음은 storage 측 — eviction 알고리즘입니다."

---

## Part 7. Mechanism 2 — Previous-answer-based Eviction — 8분

### Slide 19. Reuse distance와 answer length — `33:00–35:00` (2분)

- **핵심 메시지**: 이전 라운드 답변이 길수록 다음 KV access의 *weighted reuse distance 하한*이 함께 증가한다 (Spearman ρ = 0.94 ~ 0.98).
- **발표 멘트**
  > "Mechanism 2를 시작하기 전에, 한 가지 핵심 관찰부터 짚겠습니다.
  >
  > Figure 12는 12개의 시간대(아침 8시부터 저녁 7시까지)에서 한 가지 상관관계를 측정한 결과입니다. 가로축이 *이전 라운드의 답변 토큰 길이*, 세로축이 *다음 KV access의 weighted reuse distance*입니다. 빨간 곡선이 그 *하한* 라인입니다.
  >
  > 핵심은 — 12개 시간대 모두에서 *같은 패턴*이 나옵니다. 이전 답변이 길수록, 다음 access의 reuse distance 하한이 *함께 증가*합니다. Spearman 순위 상관계수로 측정하면 *0.94에서 0.98 사이* — 매우 강한 양의 상관관계입니다.
  >
  > 직관은 단순합니다. 답변이 길면 사용자가 그걸 *더 오래 읽습니다*. 그 시간 동안 다른 사용자들의 요청이 끼어들고, 다른 KV들이 access 됩니다. 그래서 다음 access가 일어날 때쯤이면 reuse distance가 *최소* 그만큼 커져 있을 수밖에 없습니다.
  >
  > 이건 *인터랙티브 워크로드*에 *본질적으로 깔린* 신호입니다. *human-in-the-loop* 시스템이라면 어디에든 적용 가능한 일반적인 관찰이고, 다른 도메인으로 확장 가능성이 있다는 점도 언급해두면 좋습니다."
- **보조 노트**
  - "왜 하한이지 평균이 아닌가?" — 답변 길이가 *최소* 그만큼 시간을 보장하기 때문. 평균이나 상한은 노이즈가 더 크다.
  - Spearman 0.94~0.98은 매우 강한 상관 — 0.7만 넘어도 강하다는 사회과학 기준과 비교.
- **이어가기**: "그런데 reuse distance가 크다고 무조건 evict 해도 되는 건 아닙니다."

---

### Slide 20. Hit potential — `35:00–37:00` (2분)

- **핵심 메시지**: Reuse distance가 *promising 영역*에 있는 access는 LRU에서는 hit이 거의 0이지만, *Belady에서는 100%* 가까이 살아 있다.
- **발표 멘트**
  > "Figure 13의 막대그래프가 핵심입니다. 가로축이 weighted reuse distance를 구간별로 자른 것이고, 세로축이 그 구간 안의 access들이 *실제로 hit 했는지*입니다. 네 가지 정책을 비교합니다 — FIFO, LRU, queue-enhanced, 그리고 *Optimal*(즉 Belady).
  >
  > 가로축을 *세 영역*으로 나눕니다. 왼쪽 — *Small reuse distance*, perf layer 크기보다 작은 구간입니다. 여기는 *어느 정책이든 hit rate가 1에 가깝습니다*. 모든 정책이 잘 합니다.
  >
  > 오른쪽 끝 — *Extreme reuse distance*, 440 GB 이상 — 여기는 *Belady도 hit를 못 합니다*. 너무 멀리 떨어져서 perf layer가 그동안 통째로 갈아치워졌기 때문이에요. 이 구간 KV는 *evict 1순위*입니다.
  >
  > 중요한 건 *Promising 구간* — 200에서 440 GB 사이입니다. 여기서 FIFO와 LRU는 hit rate가 0에서 40% 사이로 떨어지지만, *Belady는 거의 100%*에 가깝게 잡습니다. 즉 이 구간에 *살아남을 가치가 있는 KV들*이 묻혀 있는데, 단순 거리 기반 eviction은 그걸 못 살립니다.
  >
  > 결론 — 단순한 거리 기반 evict가 아니라, *구간별 hit 확률을 모델링*하는 알고리즘이 필요합니다."
- **보조 노트**
  - "Belady가 가능한가요?" — 미래를 안다는 가정이라 실시간에는 불가능. 다음 슬라이드에서 ghost cache로 *시뮬레이션*하는 방법을 보여준다고 예고.
- **이어가기**: "그러면 그 구간별 hit 확률을 어떻게 추정할 수 있을까요?"

---

### Slide 21. Ghost cache + bucketing — `37:00–39:00` (2분)

- **핵심 메시지**: Promising 영역을 *m개의 fine-grained bucket*으로 나누고, 각 bucket의 hit 확률을 *백그라운드 Belady 시뮬레이션*으로 측정.
- **발표 멘트**
  > "알고리즘은 다섯 단계입니다. 슬라이드 순서대로 따라가겠습니다.
  >
  > ① Promising 구간을 *m개의 fine-grained bucket*으로 자릅니다. 너무 거칠게 자르면 각 bucket 안에서 hit rate가 다양해서 추정이 부정확해지고, 너무 잘게 자르면 통계가 안정되지 않습니다.
  >
  > ② 각 bucket의 hit rate를 *Belady 시뮬레이션*으로 측정합니다. 그런데 이건 어떻게 가능한가? — *ghost cache* 라는 자료구조 위에서 가능합니다. ghost cache는 *실제 데이터 없이 metadata만* 가지고 있는 시뮬레이션용 cache예요. 메타데이터 단위면 메모리 부담이 작으니까, *이미 지나간 trace*에 대해 사후적으로 Belady를 돌릴 수 있습니다.
  >
  > ③ 사용자별로 *과거 KV access 분포*를 추적합니다. 이걸 사용자 단위로 묶어서, '이 사용자의 다음 access는 각 bucket에 떨어질 확률이 얼마인가'를 추정합니다.
  >
  > ④ — *여기가 bidirectional 신호의 결정적 활용점입니다*. compute가 방금 막 보낸 답변 길이를 신호로 받아서, reuse distance의 *하한*을 정합니다. 그 하한보다 작은 bucket들의 확률을 0으로 *truncate* 하고 나머지를 정규화합니다. 이로써 분포가 *날카로워집니다*.
  >
  > ⑤ 마지막으로 그 분포에 ghost cache가 알려준 bucket별 hit rate를 곱해서, 이 KV의 *overall hit potential*을 계산합니다. 다음 슬라이드의 식이 그 계산입니다."
- **보조 노트**
  - m은 hyperparameter — 논문에 명확한 값 없음. sensitivity 분석도 없음. Q&A 대비 정직하게 답.
  - ghost cache 자체는 새 발명이 아닌 캐시 시뮬레이션의 고전 기법. 그러나 LLM 워크로드에 적용한 게 새롭다.
- **이어가기**: "그 hit potential 계산식을 한 줄로 정리하면."

---

### Slide 22. Equation 2 — `39:00–41:00` (2분)

- **핵심 메시지**: 한 줄짜리 식이 small, promising bucket들, extreme의 가중합으로 evict 후보를 결정.
- **발표 멘트**
  > "식의 모양은 단순합니다 — *Overall_potential = prob_small × 1.0 + prob_extreme × 0.0 + Σᵢ prob_promising(i) × hit_promising(i)*.
  >
  > 세 항을 하나씩 짚으면 — 첫 항 *prob_small × 1.0*. 다음 access가 small 영역에 떨어질 확률에 hit rate 1을 곱한 거예요. 즉 small 영역이면 무조건 hit 한다고 가정합니다.
  >
  > 마지막 항 *prob_extreme × 0.0*. extreme 영역이면 Belady조차 hit를 못 하니까, 그 확률은 *0으로 곱해서 죽입니다*. 명시적으로 식에 박은 이유는 분포의 *합이 1*임을 명확히 하기 위해서입니다.
  >
  > 가운데 항 — *Σᵢ prob_promising(i) × hit_promising(i)*. 이게 핵심이에요. 각 promising bucket i에 대해서, 다음 access가 거기 떨어질 확률에, ghost cache가 측정한 그 bucket의 hit rate를 곱해서 더합니다. 즉 *어느 KV가 다음에 살아남을 잠재력*을 사용자별 분포와 Belady 측정치로 가중합 낸 것입니다.
  >
  > 이 potential이 *가장 낮은* KV가 evict 대상입니다. 살아남을 가능성이 가장 적은 녀석부터 내보낸다는 거죠.
  >
  > 슬라이드 아래의 회색 박스에 한 가지 — *추가 비용이 0.35 ms*. 결정 단계에 들어가는 비용입니다. 무거운 일은 다 백그라운드에서 ghost cache가 하니까 결정은 가볍습니다."
- **보조 노트**
  - 0.35 ms는 Slide 29의 overhead 분석에서 다시 등장.
  - 식에 들어가는 모든 확률이 사용자별로 분리되어 있다는 점도 강조 가능 — *user-aware* eviction의 본질.
- **이어가기**: "이제 마지막 메커니즘 — 어떤 텐서를 캐싱할지의 트레이드오프."

---

## Part 8. Mechanism 3 — Storage-Efficient Tensor — 3분

### Slide 23. Tensor cost efficiency — `41:00–42:30` (1분 30초)

- **핵심 메시지**: KV tensor를 캐싱하는 건 *최선이 아니다*. 정규화된 activation(tensor 6)이 *cost efficiency 51 GFLOPs/MB*로 KV(30.5)의 1.67배.
- **발표 멘트**
  > "Mechanism 3는 약간 다른 종류의 트레이드오프입니다. *어떤 텐서를 캐싱할지*에 대한 분석이에요.
  >
  > 이 논문은 새 metric을 정의합니다 — *Cost efficiency = Saved compute / Required space*, GFLOPs per MB 단위입니다. 같은 공간에 캐싱했을 때 얼마나 많은 compute를 절약할 수 있는지의 비율이죠.
  >
  > Figure 14를 보면 — (a)에서 layer 안의 여섯 가지 intermediate tensor와 KV tensor를 비교하고 있습니다. (b)가 cost efficiency 곡선인데, *tensor 6에서 정점*을 찍습니다. *tensor 6는 정규화된 activation* — FFN 직전, 그러니까 다음 layer의 LayerNorm 입력 단계의 텐서입니다.
  >
  > 수치로는 — *tensor 6가 51 GFLOPs/MB*, KV tensor가 *30.5 GFLOPs/MB*. 즉 같은 공간에 *1.67배* 더 많은 compute를 절약합니다.
  >
  > tensor 6에서 KV로 되돌리려면 변환이 필요하지만, *GPU 1 step*이면 끝납니다. overhead가 작아요. 그래서 KV 대신 tensor 6를 저장하는 게 *공간 대비 compute 절약*에서 우위입니다."
- **보조 노트**
  - "왜 굳이 tensor 6인가 — tensor 4나 5는?" — Figure 14(b)에서 cost efficiency가 정점인 게 6번. 다른 tensor들도 캐싱 후보지만 trade-off가 6번이 가장 좋다.
- **이어가기**: "그럼 모든 모델에 이득일까요? 그렇진 않습니다."

---

### Slide 24. MHA vs GQA — `42:30–44:00` (1분 30초)

- **핵심 메시지**: MHA에서는 tensor 6 캐싱이 이득, *GQA에서는 KV tensor 자체가 이미 작아서 KV를 그대로 캐싱*.
- **발표 멘트**
  > "이 메커니즘의 적용 범위는 *attention 헤드 구조*에 따라 달라집니다.
  >
  > 왼쪽 박스 — *MHA-based 모델*. Llama, Qwen, Bloom, OPT, Baichuan 같은 모델들이 여기 속합니다. head마다 K와 V가 *별도로 분리*되어 있어서, head 수만큼 KV tensor가 곱해집니다. 즉 KV가 *크고*, 그래서 tensor 6를 캐싱하면 *적은 공간으로 많은 compute*를 절약할 수 있습니다. Bidaw는 MHA 모델에서는 tensor 6를 캐시합니다.
  >
  > 오른쪽 박스 — *GQA-based 모델*. 여러 query head가 K와 V를 *공유*합니다. group 크기 g에 따라 KV tensor가 *1/g 배*로 작아져요. KV 자체가 이미 작으니까 tensor 6로 바꾸는 *변환 비용이 이점을 깎아먹습니다*. 그래서 GQA에서는 그냥 *KV tensor를 그대로 캐싱*합니다.
  >
  > 이 논문이 평가한 모델 5종은 OPT와 Qwen인데, OPT는 MHA고 Qwen은 버전에 따라 다릅니다. 청중이 *Llama-2 같은 GQA 모델에서는?* 이라고 물으면 — Mechanism 3은 비활성, 나머지 두 메커니즘은 그대로 적용됩니다."
- **보조 노트**
  - GQA 모델에서 ablation이 어떻게 변하는지 — 1.10배 (tensor caching) 효과는 사라지고, scheduling + eviction의 1.97배만 남는다.
- **이어가기**: "구현 디테일을 짧게 짚고 평가로 넘어가겠습니다."

---

## Part 9. Implementation — 1분

### Slide 25. 구현 노트 — `44:00–45:00` (1분)

- **핵심 메시지**: vLLM 위에 네 가지 기법 — continuous batching, mix-grained PagedAttention, low-priority CUDA stream, inclusive caching.
- **발표 멘트**
  > "구현은 vLLM 위에 네 가지 트릭을 얹는 형태입니다. 빠르게 짚을게요.
  >
  > 첫째, *Continuous batching*. ORCA 류의 기법으로, 조기 종료된 요청을 batch에서 즉시 release 해서 새 요청을 빨리 admit 합니다.
  >
  > 둘째, *Mix-grained PagedAttention*. 이게 좀 흥미로운데, *history와 query 토큰*은 *256 토큰의 큰 블록*으로 잡습니다 — 길이가 *이미 알려진* 토큰들이라 큰 블록이 효율적이에요. *response 토큰*은 길이가 예측 불가능하니까 *16 토큰의 작은 블록*으로 잡습니다. CPU-GPU 전송 효율도 올라가고 단편화도 줄어듭니다.
  >
  > 셋째, *Low-priority CUDA stream*. tensor 6에서 KV로 되돌리는 변환을 *별도의 low-priority 스트림*에서 실행합니다. SM이 idle 한 틈에 들어가니까 실제 추론 latency에는 영향이 없습니다.
  >
  > 넷째, *Inclusive caching*. capacity layer에 항상 복사본이 있으니까 evict는 perf layer에서 포인터만 제거하면 됩니다 — *write가 거의 0*입니다. SSD write 트래픽이 폭발하지 않는 이유예요."
- **보조 노트**
  - Mix-grained PagedAttention은 이 논문의 *부수적 contribution* — vLLM에 직접 PR 거리가 될 수도.
- **이어가기**: "이제 평가 결과를 보겠습니다."

---

## Part 10. Evaluation — 5분

### Slide 26. 실험 환경 — `45:00–46:00` (1분)

- **핵심 메시지**: 모델 5종(OPT 6.7B/13B/30B, Qwen 7B/14B), 자체 trace + ShareGPT, 베이스라인 4종.
- **발표 멘트**
  > "환경부터 짧게 — A800 80 GB 1대, host memory 200 GB, capacity layer는 RAID-5 위 4장 SATA SSD로 1.5 GB/s. PCIe는 Gen 4라 GPU 전송은 30 GB/s 정도입니다. 핵심은 — *SSD가 진짜 bottleneck*이라는 점입니다. PCIe는 충분히 빠르고, GPU-host 사이는 막히지 않습니다. 모든 부담은 SSD에서 옵니다.
  >
  > 모델은 다섯 가지 — OPT 6.7B, 13B, 30B 그리고 Qwen 7B, 14B. 워크로드는 둘 — 자체 1M 라운드 trace와 공개 ShareGPT(Poisson 시뮬). 베이스라인은 네 가지 — vLLM은 recompute, CachedAttention과 FlashGen은 KV 캐싱 SOTA, Optimal은 perf-layer-only ideal입니다."
- **보조 노트**
  - "더 빠른 SSD라면?" — Slide 27 직후에 5 GB/s 시뮬레이션 결과가 논문에 있다고 답.
- **이어가기**: "핵심 그림 — 5개 모델 동시 평가."

---

### Slide 27. Overall performance — `46:00–47:30` (1분 30초)

- **핵심 메시지**: 모델 5종 모두에서 Bidaw가 *Optimal에 거의 붙는다* — latency 최대 3.58배 단축, throughput 1.83배 향상.
- **발표 멘트**
  > "Figure 15의 다섯 패널을 한꺼번에 보시면 됩니다. 각 패널이 한 모델이고, 가로축이 도착률, 세로축이 평균 latency입니다.
  >
  > 위에서부터 — vLLM(초록 삼각형, recompute)이 가장 빨리 폭주합니다. CachedAttention(파란 오각형)과 FlashGen(빨간 사각형)이 그다음. *Bidaw(주황 동그라미)는 가장 아래의 Optimal(갈색 마름모)과 거의 평행*입니다.
  >
  > 수치 — Bidaw가 베이스라인 대비 평균 latency를 *최대 3.58배 단축*하고, 같은 latency 기준 throughput을 *1.43에서 1.83배 향상*시킵니다. Optimal 상한선에 거의 붙었다는 게 핵심입니다.
  >
  > 한 가지 강조 — Bidaw는 *lossless*입니다. 답변 정확도는 FlashGen과 동일합니다. user 1과 user 2의 처리 *순서*만 바뀌므로 각 사용자의 LLM 출력은 완전히 같습니다. 양자화나 압축 류 기법과 정반대 입장이에요."
- **보조 노트**
  - "lossless"는 발표 내내 강조해야 할 포인트 — Q&A에서 단골.
  - 1.83배는 OPT-30B 기준. 모델에 따라 다르다.
- **이어가기**: "다른 축에서도 확인합니다 — 메모리 민감도와 eviction miss rate."

---

### Slide 28. Memory sensitivity와 miss rate — `47:30–48:30` (1분)

- **핵심 메시지**: host memory가 작을수록 *격차가 더 벌어진다* — 메모리 절약 측면에서 진짜 가치가 드러남.
- **발표 멘트**
  > "왼쪽 — Figure 16, host memory 크기를 120 GB까지 줄이며 본 latency입니다. 핵심은 — Bidaw가 *120 GB host memory만으로* 베이스라인이 *200 GB에서 내는* 정도의 latency를 냅니다. 그러니까 *1.75에서 2.19배 더 많은 user/min*을 지원합니다. 메모리가 작아질수록 격차가 *더* 벌어진다는 게 중요해요.
  >
  > 오른쪽 — Figure 18, eviction miss rate 비교입니다. queue-enhanced 대비 *57.6% 단축*, FIFO나 LRU 같은 일반 정책 대비 *69.9% 단축*. Mechanism 2가 단독으로 만든 격차입니다."
- **보조 노트**
  - "메모리 절약" 관점은 데이터센터 비용 측면에서 의미가 크다 — 청중이 인프라 엔지니어라면 더 강조.
- **이어가기**: "마지막으로 tail latency와 내부 분해를 보겠습니다."

---

### Slide 29. Tail · Ablation · Overhead — `48:30–50:00` (1분 30초)

- **핵심 메시지**: P99까지 단축, 세 메커니즘이 곱셈으로 기여, overhead는 ms 단위로 무시 가능.
- **발표 멘트**
  > "마지막 세 그림을 한 번에 짚겠습니다.
  >
  > 왼쪽 — *Tail latency*. CachedAttention 대비 P90 *−53%*, P95 *−49%*, P99 *−47%*. 평균뿐 아니라 *분포의 꼬리*까지 잡았다는 점이 핵심입니다. dual queue의 promotion 시 *원래 도착 시각 유지*가 여기서 빛을 발합니다.
  >
  > 가운데 — *Ablation*. 세 메커니즘을 차례로 켜면서 throughput 향상을 측정했습니다. scheduling이 *1.58배*, 거기에 eviction을 더하면 누적 *1.97배*, 마지막 tensor caching까지 더하면 *2.17배*. 각 메커니즘이 *독립적으로 의미가 있다*는 증거입니다.
  >
  > 오른쪽 — *Overhead*. scheduling 결정이 0.62 ms, eviction 결정이 0.35 ms, KV 변환이 100 ms 미만. 시스템에 *안전하게 얹을 수 있는* 수준입니다.
  >
  > 정리하면 — 평균뿐 아니라 꼬리도 잡고, 세 메커니즘이 각각 기여하고, overhead는 무시 가능. 깔끔합니다."
- **보조 노트**
  - "왜 P99도 줄어드나" — promotion 시 원래 도착 시각 유지 덕분.
- **이어가기**: "마지막으로 정리하겠습니다."

---

## Part 11. Conclusion & Discussion — 3분

### Slide 30. 정리 · 한계 · 시사점 — `50:00 이후 Q&A 직전` (마지막 3분)

- **핵심 메시지**: Bidaw의 진짜 기여는 "compute와 storage가 *양방향으로* 서로의 정보를 본다"는 *설계 원칙*이다. 알고리즘 디테일은 그 원칙을 구체화한 결과.
- **발표 멘트**
  > "정리하겠습니다.
  >
  > *기여* — 첫째, *bidirectional awareness*라는 새로운 설계 원칙. 둘째, 그 원칙을 구체화한 두 메커니즘 — I/O-aware scheduling과 previous-answer-based eviction. 셋째, 부수적으로 *storage-efficient tensor caching*으로 공간과 연산의 trade-off를 정량화. 그 결과 모델 5종 평균 latency *3.58배*, throughput *1.83배*입니다.
  >
  > *한계* — 네 가지를 짚겠습니다. 첫째, *한 사용자 안에서의 KV 재사용만* 다룹니다. 사용자 간 공유는 MeanCache 류와 직교하는 다른 줄기예요. 둘째, *GQA 모델에서는 tensor caching 이점이 사라집니다*. Llama-2/3, Qwen 2.5 이후에서는 Mechanism 1, 2만 적용됩니다. 셋째, *ShareGPT처럼 timestamp가 없는 trace에서는 eviction 효과가 약해집니다* — 논문도 이 점을 인정합니다. 넷째, *단일 GPU 노드 평가*입니다. disaggregated, multi-node 환경은 future work입니다.
  >
  > *시사점* — 이 논문이 보여준 큰 그림은 단순합니다. 사용자가 *글을 읽는 속도*를 storage 정책의 *신호*로 쓸 수 있다는 일반적인 교훈. 그리고 HRRN, Belady ghost cache 같은 *고전 시스템 기법*이 LLM 워크로드에서도 여전히 살아 있다는 증거입니다. ML serving과 storage의 *co-design*이 이 영역의 후속 연구가 활발해질 방향임을 보여주는 좋은 사례입니다.
  >
  > 여기까지가 Bidaw 입니다. 질문 받겠습니다."
- **보조 노트**
  - "한계 4가지"를 *반드시* 짚는 게 청중 신뢰에 결정적이다. 한계를 발표자가 먼저 인정하면 Q&A가 부드러워진다.
  - 마지막 한 줄은 그대로 읽어도 좋다 — 발표 마무리는 짧고 명확하게.
- **이어가기**: (Q&A로 이어짐)

---

## 발표 팁 (사전 리허설용)

### 외워둘 숫자 (놓치면 발표 흐름이 무너지는 것)

- 격차: **latency 3.8배 / throughput 2배** (벤치마크 vs ideal)
- 라운드: **22.4**(평균), **45**(P90), **5.7**(ShareGPT 비교)
- Locality: **80% > 200 GB**, **hit rate ≈ 20%**
- Cost efficiency: **tensor 6 = 51, KV = 30.5 GFLOPs/MB**
- 최종 결과: **latency 3.58배, throughput 1.83배** 향상
- Tail: **P99 −47%**
- Ablation: **scheduling 1.58 → +eviction 1.97 → +tensor 2.17**
- Overhead: **scheduling 0.62 ms, eviction 0.35 ms, 변환 < 100 ms**

### 잘못 쓰기 쉬운 용어

- *Weighted* reuse distance — 그냥 횟수가 아니라 *byte 합*이다. Slide 10에서 정확히 정의해두지 않으면 §3.3 전체가 흔들린다.
- *Inclusive caching* — capacity layer에 항상 복사본이 있어서 eviction이 write-free라는 의미. FlashGen에서 차용한 기법이다.
- *Disk-HRRN* — 고전 HRRN의 service time을 *KV size*로 치환한 변형. service time 대신 size라는 점을 분명히.

### 흐름 상 중요한 전환점

- **Slide 7 → 8**: "왜 격차가 나는가? 트레이스로 직접 본다." — motivation 섹션 진입.
- **Slide 11 → 12**: 세 관찰을 *한 줄로 정리* — root cause 도입.
- **Slide 13 → 14**: 추상 원칙에서 *구체 시스템 그림*으로 — 청중이 그림과 원칙을 연결.
- **Slide 22 → 23**: Mechanism 2 마무리, Mechanism 3 진입 — 톤 전환을 명확히.

### Q&A 단골 질문

- **"GQA 모델에서는?"** → tensor caching은 비활성. 나머지 두 메커니즘은 그대로 적용. ablation 결과는 1.97배까지.
- **"왜 답변 길이가 신호로 충분한가?"** → 사용자가 답을 다 읽고 다음 질문을 만들기까지의 *최소 시간 하한*을 만들기 때문. 평균이나 상한이 아닌 *하한*.
- **"ShareGPT에서는 왜 효과가 약해지나?"** → timestamp 시뮬레이션이 Poisson이라 *답변 길이와 사용자 사고 시간의 상관관계가 깨지기 때문*.
- **"Bidaw가 lossless인가?"** → 답변 정확도는 완전히 같다. user 처리 *순서*만 바뀌므로 각 사용자의 LLM 출력은 동일.
- **"PCIe 5.0이나 더 빠른 SSD라면?"** → 논문이 5 GB/s SSD를 시뮬레이션했다. baseline은 좀 개선되지만 Bidaw와의 격차는 여전히 크다.
- **"hyperparameter (5% threshold, bucket 수 m) sensitivity는?"** → 논문이 명시적 분석을 안 했다. 정직하게 그렇게 답변.
- **"disaggregated serving (DistServe)과 결합?"** → future work라고 명시. capacity layer가 SSD가 아니라 *원격 GPU memory*인 경우, 가정(I/O 시간 ≈ KV size)을 재측정해야 한다.

### 시간이 부족할 때 줄이는 순서

1. Slide 25 (구현 노트) — 30초로 줄임
2. Slide 26 (실험 환경) — 핵심 두 줄만 (모델 5종, baseline 4종)
3. Slide 18 (스케줄링 예시) — Figure 11 (b) 결과만 짚고 넘어감
4. Slide 21 (5단계 알고리즘) — 5단계 모두 말고 ④번 핵심만

### 시간이 남을 때 더 깊이 들어갈 곳

1. Slide 19 — Spearman 0.94~0.98이 어느 정도로 강한지, 사회과학 기준선과 비교
2. Slide 23 — tensor 6의 정확한 위치(FFN 직전 LayerNorm 출력) 추가 설명
3. Slide 27 — Optimal과의 절대 격차를 패널별로 짚기
