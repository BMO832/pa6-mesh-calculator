# PA6 Mesh Calculator V2

V1과 별도의 앱입니다. 루트의 V1 코드·의존성·배포 설정을 변경하지 않습니다.
`mesh_engine.py`는 V1의 바이트 단위 동일 복사본이며, 새 용출 계산은 `leaching.py`로 분리했습니다.

## 실행 / 배포

프로젝트 루트에서 `python -m streamlit run v2/app.py`.
Streamlit Community Cloud에서 **새 앱**을 만들고 같은 저장소의 `main`, 진입점 `v2/app.py`, Python 3.12를 선택합니다.
V2 의존성은 `v2/requirements.txt`이며 기존 루트 의존성을 수정하지 않습니다.
V1 주소: https://pa6-mesh-calculator-bmo832.streamlit.app/

## 모델

- 밀도 초기 가정값 ρ=1,130 kg/m³, d는 mm→m 변환, T는 전체 필라멘트 길이(m).
- `m = ρ × πd²/4 × T` (kg). 매몰률을 적용하지 않습니다.
- `r(t) = 0.653 × (1 − 0.771 exp(−0.407t))` (%), t=1~64 day, 기본 7일, 30°C 고정.
- `M = m × r/100 × 1,000,000` (mg).
- `q = M/A_total` (mg/m²). 분모는 매몰 **전** 전체 기하학적 표면적입니다.
- 0일은 양의 절편 문제로 입력에서 제외합니다. 내부 반올림 없이 네 자리로 출력합니다.

지시서에 제공된 경험식과 계수를 그대로 사용합니다. 출처는 Bridson et al. (2023),
*Release of additives and non-intentionally added substances from microplastics under environmentally relevant conditions*,
Environmental Advances, DOI: https://doi.org/10.1016/j.envadv.2023.100359.

이는 30°C 수중 PA6 플라스틱 조각 실험을 재활용 PA6 모노필라멘트에 적용한 참고 시나리오입니다.
실제 해변 또는 재활용 모노필라멘트에 대한 검증 결과가 아닙니다.
50% 매몰은 표면적 출력에만 적용하며 질량·용출량을 절반으로 줄이지 않습니다.
q는 질량 기준 예측의 면적 환산값이지 실제 면적당 용출 실험값이 아닙니다.
직조 구조·직경에 따른 용출속도 차이, 온도 변화, UV, 실제 침수 조건을 고려하지 않습니다.
온도 보정, 활성화에너지, 환경농도 및 위해성 평가는 구현하지 않습니다.

## 검증

프로젝트 루트에서 `python -m unittest v2.test_v2 -v`.
V1 파일 해시 보존, 엔진 복사본·두 구조 결과 일치, 질량 단위 변환, %→mg 변환,
전체 면적 분모, 1~64일 범위·증가성·오류 입력, 슬라이더 변경 시 기존 계산 유지 검증.
`v1_hashes.json`은 V1 파일의 상대 경로와 변경 전 해시를 보관합니다.

계수 교차 확인: 저자의 [Canterbury 연구자료 Table 4-4](https://ir.canterbury.ac.nz/server/api/core/bitstreams/c54d6496-61cd-41d2-b45a-e2d46fcaef8d/content)에서 PA6_HAS 카프로락탐의 Ce=0.653%, A=0.771, k=0.407/day를 확인했습니다. 본 앱은 계수 불확실성 없이 지시서의 점 추정식만 사용합니다.
