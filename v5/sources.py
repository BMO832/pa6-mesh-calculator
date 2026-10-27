"""Evidence registry: a reference is not automatically the source of our equation."""
SOURCES = {
 'team': ('D · 연구팀 가정 및 설계값','연구팀 V5 개발 지시문 (2026)',None,
          '매몰률·이동유지율·포화도·균일혼합·경로계수·리브·회수율. 현장/시료 실측 후 보정 필요. 문헌 검증값 아님.','사용자 지시문'),
 'geometry': ('B · 기본 수학·기하학 공식','원통 측면적·체적·질량/부피 정의 (일반 공식)',None,
              'A=πdT, V=πd²T/4, m=ρV 및 단위 환산. 별도 원 논문 없음. 실제 형상·밀도 실측 필요.','수학적 정의'),
 'grid': ('C · 기존 이론을 참고한 자체 유도식','Belleville Wire Cloth, Resources (연도 미표기)',
          'https://www.bwire.com/resources/','직조·평직 설명 참고. 경계 포함 가닥 수와 길이 합산식은 프로그램 자체 유도. 실제 상하 굴곡·접촉면 미보정.','페이지 확인'),
 'clip': ('C · 기존 이론을 참고한 자체 유도식','Line Clipping in 2D: Overview, Techniques and Algorithms (2022)',
          'https://doi.org/10.3390/jimaging8100286','클리핑 이론 개관 참고. 실제 코드는 직선 매개변수의 축별 허용구간 교집합을 사용. 특정 Liang-Barsky 구현을 직접 사용했다고 주장하지 않음.','출판/DOI 정보 확인'),
 'weave': ('C · 자체 구조식 / D · 설계계수','Peirce (1937), The Geometry of Cloth Structure',
           'https://doi.org/10.1080/19447023708658809','일반 직물 굴곡의 이론적 참고. 짚신형 식, k=1.6, c_w=1.05, d_rib=d_f+h, 5회 주기, 회수율 60%의 직접 출처가 아님. 모두 팀 가정으로 실측 보정 필요.','출판사 관련 서지 확인; 원문 직접 접근 제한'),
 'roll': ('B · 원환 면적 기하학 유도 / D · 유효 두께 가정','RollSpec, How to Calculate Roll Diameter and Web Length (2026)',
          'https://rollspec.com/guides/roll-diameter-length/','원환 단면과 Lt의 등가 관계 참고. 심지관은 외경, 기본 0.15 m. 감김 공극·압축·장력 미반영. 기본/리브 두께별 별도 이상화 추정.','페이지 수식 확인'),
 'density': ('D · 대표 가정값 (물성자료 참고)','NETZSCH, PA6: 폴리아미드 6 (연도 미표기)',
             'https://analyzing-testing.netzsch.com/ko/polrimeo-netzsch-com/engineering-thermoplastics/pa6-polyamide-6','자료 밀도 범위 1.12-1.15 g/cm³. 1130 kg/m³는 이 범위의 대표 가정값이며 재생 원사 실측 아님.','물성 범위 확인'),
 'bridson': ('A · 문헌 기반 경험식','Bridson et al. (2023), Release of additives and non-intentionally added substances from microplastics under environmentally relevant conditions, Table 4',
             'https://doi.org/10.1016/j.envadv.2023.100359','30°C PA6 질량 대비 용출률 계수. 올리고머 반정량. 플라스틱 조각→모노필라멘트 적용은 추정. 65-92일은 외삽이며 최대 용출량 보장이 아님.','V4 계수 유지·지시문 대조'),
 'decay': ('B · 기본 1차 반응속도론 / D · 반감기 시나리오','Fortmann & Rosenberg (1984), Fate of ε-caprolactam in the aquatic environment',
           'https://doi.org/10.1016/0045-6535(84)90008-0','수중 분해의 조건 의존성 참고. 5·9.5·14일을 직접 실측값으로 확인하지 못함. 모래 반감기 아님. λ=ln2/H 및 날짜 말 투입은 수학/프로그램 가정. 실측 보정 필요.','수중 특성 초록 확인; 선택값의 직접 근거 미확인'),
 'kubo': ('A · 관련성 참고 / D · 가상 반감기','Kubo et al. (2025), Iterative Synthesis and Marine-Biodegradation Assessment of Discrete Oligomers Based on Poly(Butylene Succinate), Poly(Ethylene Terephthalate), Polyamide 6, and Polyisoprene',
          'https://doi.org/10.1021/acs.macromol.5c01531','선형 PA6 올리고머의 해양 생분해 가능성 참고. 고리형 올리고머 환경 반감기는 제공하지 않음.','V4 참고문헌 유지'),
 'soil': ('B · 밀도와 공극률의 정의 / D · 기본 밀도 가정','Kansas State University, Soil Density, Soils Laboratory Manual (연도 미표기)',
          'https://kstatelibraries.pressbooks.pub/soilslabmanual/chapter/soil-density/','공극률=1-용적밀도/입자밀도 관계 참고. 1500·2650 kg/m³는 현장 실측 전 가정값이며 포화도와 공극률은 다름.','색인 확인; 직접 페이지 접근 제한'),
 'anzg': ('A · 노출 관련 이론 참고 / D · 자체 배분 모델','ANZG, Methodology for deriving toxicant guideline values for sediments (웹 연도 미표기)',
          'https://www.waterquality.gov.au/anz-guidelines/guideline-values/derive/field-effects/method-toxicants-sediments','퇴적물 독성 및 평형분배 접근의 관련성 참고. 본 매몰부 질량배분·완전용존 혼합식을 검증한 자료가 아님.','기관 페이지 확인'),
 'epa': ('A · 노출 관련 참고','US EPA, Toxicity Testing and Ecological Risk Assessment Guidance for Benthic Invertebrates (공식 PDF)',
         'https://www.epa.gov/sites/production/files/2015-08/documents/toxtesting_ecoriskassessmentforbenthicinvertebrates.pdf','저서무척추동물 독성평가 배경자료. 본 모델의 물질별 흡착·실제 공극수 이동을 제공하지 않음.','공식 PDF 확인; 발행연도 별도 확인 필요'),
 'slu': ('미확인 참고 링크 (계수 근거로 사용하지 않음)','SLU 제공 PDF 링크 (파일명 2024)',
         'https://pub.epsilon.slu.se/35309/1/mingot-soriano-a-m-et-al-20241004.pdf','현재 기관 연구포털로 연결되어 해당 문서·수치 확인 불가. 밀도 또는 포화도를 이 자료의 실측값으로 인용하지 않음.','원문 링크 재확인 필요'),
 'crab': ('A · 굴 형성 배경 참고 / D · 깊이 시나리오','Physical constraints on sand crab burrows: Mechanical properties of wet sand explain the size and spatial distributions of burrows on beaches (2019)',
          'https://pmc.ncbi.nlm.nih.gov/articles/PMC6494038/','모래 수분과 굴 형성의 관련성 참고. 14.4·37.6 cm의 생물종·대표값 산정은 이번 확인에서 확정하지 못함.','논문 서지 확인; 깊이값 출처 확인 필요'),
 'amphipod': ('A · 생태 배경 참고 / D · 깊이 시나리오','Tsubokura et al. (1997), Seasonal Horizontal and Vertical Distribution Patterns of the Supralittoral Amphipod Trinorchestia trinitatis in Relation to Environmental Variables',
              'https://doi.org/10.1163/193724097X00107','Trinorchestia trinitatis의 수분·온도 및 계절적 분포 참고. 특정 14.4·37.6 cm가 이 종의 대표 깊이라는 근거 미확인.','출판사 초록 확인'),
 'oecd': ('A · 문헌 PNEC / B · 참고비율 환산','OECD SIDS, ε-Caprolactam (2001 평가; UNEP 간행)',
          'https://hpvchemicals.oecd.org/ui/handler.axd?id=C1609721-9FDF-4D5F-8F15-FB4F50710C72','녹조류 Scenedesmus subspicatus EC50 130 mg/L ÷ 평가계수 1000 = 0.13 mg/L (130 µg/L). 수환경 자료이며 조상대 대상종 직접 기준 아님.','OECD 원문 색인에서 산출 문장 확인'),
 'aba': ('A · 기관 기준 참고 / D · 팀 목표','US Access Board, ABA Chapter 10, 1018.4·1018.6 (현행 웹 확인 2026-10-27)',
         'https://www.access-board.gov/aba/chapter/ch10/','해변 접근로 유효폭 1525 mm, 개구부는 지름 13 mm 초과 구 통과 금지. 한국 현장 적용 별도 검토. 10·6.5 mm는 법적 기준이 아닌 팀 목표.','기관 본문 확인'),
}
PW_LABEL='전량 용존 가정의 공극수 환산농도 (mg/L)'
PW_NOTE='본 결과는 매몰부 유래 용출물이 설정한 모래층의 공극수에 모두 용존하고 균일하게 혼합된다고 가정한 환산농도이다. 모래 입자 흡착, 실제 용해도, 물질 이동 및 유실은 반영하지 않았다.'
BURROW_NOTE='이 값은 해당 깊이까지의 공극수가 균일하게 혼합된다는 가정에 따른 참고 농도이며, 실제 굴 내부의 용존 농도나 개체의 체내 흡수량을 의미하지 않는다.'
HALF_NOTE='5-14일 및 산술적 중간값 9.5일은 수중 관련 참고 시나리오이며 조상대 실측 반감기가 아닙니다. 원 논문이 세 선택값을 직접 제시했다고 확인하지 못했습니다.'
HYPOTHETICAL='본 반감기는 해당 올리고머에서 직접 측정된 값이 아니다. 카프로락탐의 수중 분해 반감기 범위를 차용한 가상 민감도 분석이다.'
LIMITS='''모든 기본 설정은 실측 이전의 가정이며 현장에서 검증된 대표 조건이 아닙니다.
공극수 구획과 V4 방식의 전체 잔존량 모래 부하량은 독립된 대안 지표이며 서로 합산하지 않습니다. mg/kg는 모래 입자 흡착농도가 아닙니다.
각 깊이는 표면부터 해당 깊이까지의 독립 완전혼합 시나리오이며 실제 수직 농도분포가 아닙니다. 130 cm는 탐색 상한입니다.
날짜 말 신규 투입, 경험식의 양의 절편을 포함한 첫날 M(1), 수지용 M(0)=0을 사용합니다.
일별 농도의 산술평균은 연속시간 시간가중 노출량이나 생물 흡수량을 직접 의미하지 않습니다.
흡착·분배·실제 용해도·침전·강우·조석·확산·유실·증발·굴의 수리학적 연결성·체내흡수·물질 간 전환은 모델링하지 않습니다.
온도 30°C 고정. 1-64일은 실험 범위, 65-92일은 경험식 외삽입니다. 수중 접촉 기간은 실제 해변 설치기간과 자동으로 같지 않습니다.
전체 용출량은 매몰률과 무관합니다. 공극수 유입량에만 f_bur×eta를 한 번 적용합니다.
매몰 표면 전체가 지속적으로 젖어 있다는 뜻이 아니며, 공극수 접촉 가능 영역은 기하학적 가정입니다.
잔류 가정은 손실을 무시하지만 균일혼합은 국소 고농도를 희석할 수 있어 최대 노출농도 또는 안전 상한이 아닙니다.'''
PNEC_NOTE='''카프로락탐만 비교합니다. 단위가 같아도 염분·노출시간·생물종·노출경로가 다릅니다.
OECD 수환경 PNEC는 달랑게류·긴꼬리도약옆새우류의 직접 독성 기준이 아닙니다.
비율 1 미만은 제품 안전 확정이 아니며 1 초과는 실제 생태계 피해 발생의 증거가 아닙니다.
교수님 검토용 참고 지표이며 법적 합격·불합격 또는 안전·위험 판정을 하지 않습니다.
고리형 올리고머에는 해당 물질의 독성 기준 미확보로 PNEC나 참고비율을 부여하지 않습니다.'''


def explain(*keys):
    import streamlit as st
    for key in keys:
        kind,title,url,scope,status=SOURCES[key]
        st.caption(kind)
        st.markdown(f'출처: [{title}]({url})' if url else f'출처: {title} · 별도 DOI 없음')
        st.caption(scope+' 확인 상태: '+status)
