BRIDSON = ('Bridson et al. (2023), *Release of additives and non-intentionally added '
           'substances from microplastics under environmentally relevant conditions*, '
           'Environmental Advances 12, 100359, Table 4. '
           '[DOI](https://doi.org/10.1016/j.envadv.2023.100359)')
FORTMANN = ('Fortmann & Rosenberg (1984), *Fate of ε-caprolactam in the aquatic environment*, '
            'Chemosphere 13(1), 53–65. [DOI](https://doi.org/10.1016/0045-6535(84)90008-0)')
KUBO = ('Kubo et al. (2025), *Iterative Synthesis and Marine-Biodegradation Assessment of '
        'Discrete Oligomers Based on Poly(Butylene Succinate), Poly(Ethylene Terephthalate), '
        'Polyamide 6, and Polyisoprene*, Macromolecules 58, 8649–8657. '
        '[DOI](https://doi.org/10.1021/acs.macromol.5c01531)')
HALF_NOTE = ('5~14일은 관련 환경 거동 자료의 참고 추정 범위를 적용한 시나리오이며 조상대 모래 실측값이 아닙니다. '
             '9.5일은 5일과 14일의 산술적 중간값입니다. 원 논문이 이 세 선택값을 직접 제시한 것으로 해석하지 않습니다. '
             '공개 초록에서 수중 분해의 조건 의존성은 확인했으나 5~14일 수치 범위 자체는 원문에서 독립 확인하지 못했습니다.')
HYPOTHETICAL = ('본 반감기는 해당 올리고머에서 직접 측정된 값이 아니다. '
                '카프로락탐의 수중 분해 반감기 범위를 차용한 가상 민감도 분석이다.')
LIMITS = '''모든 결과는 문헌의 수중 PA6 플라스틱 조각 용출 경험식을 이동로 모노필라멘트에 적용한 참고 시나리오입니다.
온도는 30°C 고정이며 실제 해변의 방출량을 검증한 결과가 아닙니다. 접촉 기간은 실제 해변 설치기간과 자동으로 같지 않습니다.
50% 매몰은 표면적 출력에만 적용하며 PA6 질량이나 용출량·잔존량을 절반으로 줄이지 않습니다.
직경·직조 구조에 따른 실제 용출속도 차이와 올리고머 간 전환 반응은 모델링하지 않습니다.
분해 후 잔존량 전량이 매트 아래 혼합층에 남아 균일하게 배분된다고 가정합니다.
깊이별 값은 0~해당 깊이층 평균의 독립된 대안 시나리오이며 실제 수직 농도분포나 그 깊이 지점의 농도가 아닙니다.
130 cm는 탐색 상한이지 실제 오염 도달 깊이가 아닙니다.
강우·침투·지하수·확산·흡착·이동·유실·생물흡수는 모델링하지 않습니다.
손실을 무시하는 잔류 가정과 달리 균일 혼합은 국소 고농도를 희석할 수 있으므로 최대 노출농도 또는 안전성을 보장하는 상한이 아닙니다.
mg/L 수중 독성값과 mg/kg 모래 농도를 직접 비교할 수 없습니다. 체내농도·위해지수·안전/위험 판정은 계산하지 않습니다.'''
