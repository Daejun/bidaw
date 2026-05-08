# Bidaw 예상 질문 10선 (간략판)

전체 30문항 중 발표 방어에 가장 자주 쓸 핵심 10개. 입으로 답할 수 있어야 한다.

---

### Q1. *Weighted* reuse distance가 그냥 거리(횟수)랑 어떻게 다른가?
> 횟수가 아니라 **byte 단위**다. 두 access 사이에 끼어든 *다른 KV의 총 byte 합*. Cache 압력은 byte로 표현해야 perf layer 크기와 직접 비교된다 ("80 % > 200 GB").

### Q2. 단순 prefetch / overlap이 안 되는 이유?
> GPU iteration ≈ 수십 ms, capacity-layer I/O ≈ 수백 ms. 한 iteration overlap으론 *일부만* 가려진다. 결국 **큐 자체**를 재구성해야 한다.

### Q3. disk-HRRN이 원래 HRRN과 다른 점은?
> Service time을 **KV size**로 대체. 가정: capacity-layer I/O 시간 ≈ KV size / SSD bandwidth. 식은 `R = 1 + waiting / size`로 동일.

### Q4. 답변 길이 ↔ reuse distance ρ = 0.94–0.98 — 무엇과 무엇의 상관인가?
> 답변 길이 vs reuse distance의 **하한**. 평균이 아니다. 답변이 길수록 사용자 사고 시간이 길고, 그 사이 다른 사용자 KV가 *최소* 그만큼 끼어든다.

### Q5. Belady's algorithm은 미래를 알아야 하는데 ghost cache에서 *왜 가능한*가?
> Ghost cache는 *지나간 trace*만 가지고 있다. 그 trace에 대해선 미래(=현재)를 이미 알고 있으므로 Belady가 사후적으로 시뮬레이션 가능. 그 측정값을 다음 access의 hit 확률 추정치로 사용.

### Q6. Equation 2의 세 항을 설명하라.
> `prob_small · 1.0 + prob_extreme · 0.0 + Σ_i prob_promising(i) · hit_promising(i)`.
> Small region(< perf layer 크기) → hit 확률 1, extreme(> 440 GB) → 0, promising은 bucket별 *Optimal hit rate × 그 bucket에 떨어질 확률*. 가장 낮은 potential의 KV를 evict.

### Q7. Tensor 6가 KV tensor보다 좋은 *수치적* 근거?
> Cost efficiency (saved compute / required space): Tensor 6 = **51 GFLOPs/MB**, KV = 30.5. 같은 host DRAM 공간에서 1.67× compute를 절약.

### Q8. GQA에서 Mechanism 3을 비활성화하는 이유?
> GQA는 query head들이 K,V를 공유 → KV tensor 자체가 1/g 작아진다. 변환 비용은 그대로라서 cost-efficiency 우위가 사라진다. → KV 캐시가 더 이득.

### Q9. ShareGPT에서 효과가 약해지는 이유?
> ShareGPT는 사용자 timestamp가 없어 **Poisson 시뮬**로 시간 보간. 이 시뮬은 *답변 길이 ↔ 사고 시간*의 상관을 깬다. 따라서 compute → storage 신호의 정확도가 떨어져 eviction 효과가 약화된다 (Scheduling은 영향 적음).

### Q10. Bidaw가 *lossless*인가? 답변 정확도가 바뀌나?
> 답변 정확도는 **그대로**. Scheduler는 user1·user2의 처리 *순서*만 바꾸고 각 요청 안의 LLM 출력은 그대로다. 압축/양자화류와 정반대 입장.

---

## 답변 자세 (한 줄)

- 모르는 부분은 *모른다고*. ("논문이 명시하지 않았습니다.")
- 한계는 *미리 인정* — 신뢰가 올라간다.
- 핵심 숫자(3.58× / 1.83× / 22.4 / 0.94 / 51 vs 30.5)는 *막힘 없이* 나와야 한다.
