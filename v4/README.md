# PA6 Mesh Calculator V4

V1~V3의 파일·진입점·의존성·배포 설정을 수정하지 않는 독립 Streamlit 앱입니다. 신규 파일은 모두 `v4/`에 있습니다.

## 실행과 배포

저장소 루트에서 Windows PowerShell:

```powershell
& '.\.venv\Scripts\python.exe' -m streamlit run v4/app.py --server.port 8504
```

브라우저: http://localhost:8504

일반 Python 환경에서는 `python -m pip install -r v4/requirements.txt` 후
`python -m streamlit run v4/app.py`를 실행합니다. 기존 환경에 추가 라이브러리를 설치하지 않았습니다.

독립 Cloud 배포 설정: 저장소 `BMO832/pa6-mesh-calculator`, 브랜치 `main`,
진입 파일 `v4/app.py`, Python 3.12. 기존 앱의 진입 파일을 바꾸지 않고 새 앱으로 생성합니다.
예정 URL: https://pa6-mesh-calculator-v4-bmo832.streamlit.app/
실제 배포 결과는 `DEPLOYMENT.md`에 기록합니다.

## 파일 구성

- `app.py`: 자동 갱신되는 좌우 화면, 비교 그래프, CSV
- `model.py`: 5종 용출률·일별 잔존량·통합 계산 결과
- `panel.py`: 같은 결과 객체로 표시하는 LaTeX 수식·대입값·출처
- `sources.py`: 문헌 정보와 가정·불확실성 안내
- `mesh_engine.py`, `leaching.py`: V3 계산 모듈의 바이트 동일 사본
- `sand.py`: V3 질량배분 계산 재사용. 모델 설명 문구만 잔존량 기준으로 변경
- `preview.py`: 기존 2D 직조 미리보기 함수 재사용
- `requirements.txt`: 기존 버전과 같은 Streamlit 의존성
- `test_v4.py`, `preserved_hashes.json`: 회귀·수지·화면 통합 검증, 기존 파일 보존 기록

## 계산 및 해석

기하학은 V1~V3와 동일합니다. 직교 격자의 선 개수는 floor(W/s)+1, floor(L/s)+1이고,
회전 격자는 (0,0)을 기준으로 45도 회전한 직선을 매트 경계로 클리핑합니다.
중심선이 경계 안에 있는 길이를 합산합니다. 원통 끝단·교차부 중복·접촉·굴곡은 보정하지 않습니다.
50% 매몰은 전체 원통 표면적의 절반을 가리는 이상화된 가정이며 질량이나 용출량에 적용하지 않습니다.

PA6 질량은 1130 × π(d_mm/1000)²/4 × T kg입니다.
질량 대비 누적 용출률은 Ce(1−a exp(−kt)) %, M = m_PA6 × r/100 × 10⁶ mg입니다.
30°C, 1~64일에 한정합니다. 고리형 올리고머 4종의 용출량은 반정량 결과입니다.

| 물질 | Ce (%) | a | k (day⁻¹) |
|---|---:|---:|---:|
| Caprolactam | .653 | .771 | .407 |
| PA6 cyclic dimer | .065 | .873 | .051 |
| PA6 cyclic trimer | .374 | .879 | .050 |
| PA6 cyclic tetramer | .526 | .900 | .042 |
| PA6 cyclic pentamer | .221 | .939 | .026 |

환경 분해는 λ=ln(2)/H를 사용하며 용출계수 k와 별개입니다.
경험식의 양의 절편을 인정하되 일일 수지에서는 M(0)=0으로 설정하고 첫날 신규 용출량을 M(1)로 처리합니다.
각 날짜 말에 신규 용출된 것으로 근사합니다.
R(t)=Σ[j=1..t] ΔM(j) exp(−λ(t−j)); 엔진은 동등한 재귀식 R(t)=R(t−1)exp(−λ)+ΔM(t)로 계산합니다.
분해 미반영이면 R=M입니다. 올리고머 사이의 전환 생성물은 계산하지 않습니다.

카프로락탐 기본 반감기는 9.5일, 올리고머 기본은 분해 미반영입니다.
5·9.5·14일은 수중 환경 거동 자료의 참고 추정 범위를 적용한 시나리오이고 모래 실측값이 아닙니다.
9.5일은 산술적 중간값입니다. 원 논문에서 세 선택값을 직접 제시했다고 해석하지 않습니다.
공개 초록으로 분해의 조건 의존성은 확인했으나 5~14일 수치 범위 자체를 원문에서 독립 확인하지 못했습니다.
올리고머에 선택한 반감기는 카프로락탐 범위를 차용한 가상 민감도 분석입니다.

소재 면적당 누적 용출량은 M/A_total, 평면면적당 누적 용출량은 M/(L×W)입니다.
모래 평균농도는 **R/[ρb×(L×W)×(h_cm/100)] mg/kg dry sand**입니다.
잔존량 전량이 지정층에 균일하게 배분되는 독립 시나리오이며 특정 깊이의 실제 농도분포가 아닙니다.
분해 미반영을 고르면 기존 V3 카프로락탐 결과와 일치합니다.
표층·선택 깊이·참고 평균/최대 굴 깊이의 농도를 별도로 표시합니다.
14.4·37.6 cm의 원문 및 평균/최대 구분은 저장소에서 확인되지 않아 사용자 제공 참고값으로 표시합니다.
130 cm도 원문 미확인 참고값이자 탐색 상한이며 실제 오염 도달 깊이가 아닙니다.

1130 kg/m³ 소재 밀도 및 1500 kg/m³ 건조 모래 용적밀도는 가정값입니다.
수중 플라스틱 조각 실험을 재활용 모노필라멘트에 적용하며 실제 해변에서 검증된 방출·농도 모델이 아닙니다.
접촉 기간은 실제 해변 설치기간과 자동으로 같지 않습니다.
온도 변화·UV·침수·강우·침투·확산·지하수·흡착·유실·생물흡수는 고려하지 않습니다.
전량 잔류는 손실을 무시하지만 균일 혼합은 국소 고농도를 희석할 수 있어 최대 노출농도나 안전 상한이라고 부르지 않습니다.
수중 mg/L 독성값과 모래 mg/kg를 직접 비교하지 않습니다. 체내농도·위해지수·안전 판정은 구현하지 않습니다.
내부 계산을 반올림하지 않으며 화면 숫자만 표시 정밀도로 반올림합니다.

## 출처

- Bridson et al. (2023), *Release of additives and non-intentionally added substances from microplastics under environmentally relevant conditions*, Environmental Advances 12, 100359, Table 4. https://doi.org/10.1016/j.envadv.2023.100359 — 30°C 용출식 및 계수.
- Fortmann & Rosenberg (1984), *Fate of ε-caprolactam in the aquatic environment*, Chemosphere 13(1), 53–65. https://doi.org/10.1016/0045-6535(84)90008-0 — 수중 분해 특성의 근거, 모래 실측 반감기 아님.
- Kubo et al. (2025), *Iterative Synthesis and Marine-Biodegradation Assessment of Discrete Oligomers Based on Poly(Butylene Succinate), Poly(Ethylene Terephthalate), Polyamide 6, and Polyisoprene*, Macromolecules 58, 8649–8657. https://doi.org/10.1021/acs.macromol.5c01531 — 선형 PA6 올리고머의 가속 해양 생분해 가능성 참고, 고리형 환경 반감기로 사용하지 않음.
- 모래 질량배분, 날짜 말 투입, 밀도·깊이 가정은 프로그램 정의이며 문헌에서 검증된 현장 모델로 인용하지 않습니다.

## 검증

저장소 루트에서 `python -m unittest v4.test_v4 -v`.
기존 V3가 있는 로컬 작업 사본에서 파일 보존 및 버전 일치 검사까지 실행할 수 있습니다.
공개 저장소에 V3가 없다면 해당 보존 테스트는 로컬 전체 작업 사본에서 실행해야 합니다.

자동 검증: 5종×4반감기×64일 질량수지, 계수·단위, 누적량 비감소, 반감기 순서,
독립 합산식 대조, 분해 미반영의 V3 일치, 잘못된 입력 거부,
모든 입력 변경에 따른 수식 패널·표·그래프·CSV 값 일치 및 기존 파일 SHA-256 보존.
