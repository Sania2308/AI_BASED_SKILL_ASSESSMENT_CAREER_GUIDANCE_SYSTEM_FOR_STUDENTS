from app.config import CAREER_CATALOG

def calculate_career_matches(extracted_skills, verified_skill_map, overall_assessment, preferred_career=None):
    """
    Explainable AI Career Recommendation Engine with Progressive Gating:
    
    STATE 1 — New Student (No resume + no assessment):
      Career recommendation = Not Available. Returns empty list.
      
    STATE 2 — Resume Analyzed Only:
      Career recommendations = 'Preliminary Career Match', based purely on detected skills.
      
    STATE 3 — Resume + Overall Assessment:
      Career recommendations = 'Career Match', based on detected skills and 5-domain scores.
      
    STATE 4 — Resume + Overall Assessment + Technical Verification:
      Career recommendations = 'Verified Career Readiness', based on extracted skills,
      domain scores, and verified technical tests.
      
    No default/baseline 15% floor is awarded.
    """
    has_resume = bool(extracted_skills)
    has_overall = bool(overall_assessment and any(overall_assessment.get(k, 0) > 0 for k in ["overall", "technical", "problem_solving", "communication", "domain_knowledge", "learning_ability"]))
    has_technical = bool(verified_skill_map)

    # STATE 1: Insufficient student evidence -> Gated (Not Available)
    if not has_resume and not has_overall and not has_technical:
        return []

    # Determine progressive analysis state
    if has_technical and (has_overall or has_resume):
        state_code = "STATE_4_VERIFIED"
        state_label = "Verified Career Readiness"
        state_badge = "success"
    elif has_overall and has_resume:
        state_code = "STATE_3_CAREER_MATCH"
        state_label = "Career Match"
        state_badge = "primary"
    elif has_overall:
        state_code = "STATE_3_CAREER_MATCH"
        state_label = "Career Match"
        state_badge = "primary"
    elif has_technical:
        state_code = "STATE_4_VERIFIED"
        state_label = "Verified Career Readiness"
        state_badge = "success"
    else:
        state_code = "STATE_2_PRELIMINARY"
        state_label = "Preliminary Career Match"
        state_badge = "info"

    extracted_lower = {s.lower() for s in extracted_skills}
    verified_lower = {k.lower(): v for k, v in verified_skill_map.items()}

    cat_scores = {
        "Technical Skills": overall_assessment.get("technical", 0) if has_overall else 0,
        "Problem Solving": overall_assessment.get("problem_solving", 0) if has_overall else 0,
        "Communication": overall_assessment.get("communication", 0) if has_overall else 0,
        "Domain Knowledge": overall_assessment.get("domain_knowledge", 0) if has_overall else 0,
        "Learning Ability": overall_assessment.get("learning_ability", 0) if has_overall else 0
    }

    results = []

    for role_name, config in CAREER_CATALOG.items():
        core_skills = config["core_skills"]
        total_core = len(core_skills)
        matched_skills = []
        needs_improvement_skills = []
        missing_skills = []
        weighted_points = 0.0

        for s in core_skills:
            s_low = s.lower()
            if s_low in verified_lower:
                ver = verified_lower[s_low]
                score = ver.get("score", 0)
                level = ver.get("level", "Intermediate")
                if score >= 70:
                    weighted_points += 1.0
                    matched_skills.append(f"{s} (Verified: {level})")
                else:
                    weighted_points += 0.75
                    needs_improvement_skills.append(f"{s} (Verified: {level} {score}%)")
            elif s_low in extracted_lower:
                weighted_points += 0.5
                needs_improvement_skills.append(f"{s} (Claimed, Unverified)")
            else:
                missing_skills.append(s)

        # 1. Skill coverage ratio
        skill_ratio = (weighted_points / total_core) if total_core > 0 else 0.0

        # 2. Domain alignment score
        ideal_domains = config.get("ideal_strengths", ["Technical Skills"])
        domain_avg = (sum(cat_scores.get(d, 0) for d in ideal_domains) / len(ideal_domains)) if has_overall else 0.0

        # 3. Technical benchmark factor
        min_tech = config.get("recommended_min_technical", 60)
        max_verified_score = max([v.get("score", 0) for v in verified_skill_map.values()] or [0])
        actual_tech = max(cat_scores.get("Technical Skills", 0), max_verified_score)
        tech_factor = (min(1.0, actual_tech / max(min_tech, 1))) if (has_overall or has_technical) else 0.0

        # Compute composite score by Progressive State
        if state_code == "STATE_2_PRELIMINARY":
            # State 2: Strictly based on detected skills (unverified claimed count)
            detected_core_count = sum(1 for s in core_skills if s.lower() in extracted_lower)
            composite_score = (detected_core_count / total_core) * 100 if total_core > 0 else 0.0
        elif state_code == "STATE_3_CAREER_MATCH":
            # State 3: Detected skills + overall assessment domain scores
            if has_resume:
                composite_score = (0.50 * (skill_ratio * 100)) + (0.35 * domain_avg) + (0.15 * (tech_factor * 100))
            else:
                composite_score = (0.70 * domain_avg) + (0.30 * (tech_factor * 100))
        else:
            # State 4: Verified skills + assessment domain scores + technical verification
            composite_score = (0.60 * (skill_ratio * 100)) + (0.30 * domain_avg) + (0.10 * (tech_factor * 100))

        # Apply preference bonus only if student explicitly set this target career
        if preferred_career and preferred_career.lower() == role_name.lower():
            composite_score = min(99, composite_score + 3)

        # No arbitrary 15% floor!
        match_pct = round(min(99, max(0, composite_score)))

        # Progressive readiness classification
        if state_code == "STATE_2_PRELIMINARY":
            if match_pct >= 60:
                readiness = "High Preliminary Match"
                readiness_badge = "info"
            elif match_pct >= 25:
                readiness = "Preliminary Match"
                readiness_badge = "info"
            elif match_pct > 0:
                readiness = "Low Preliminary Match"
                readiness_badge = "secondary"
            else:
                readiness = "No Matching Skills"
                readiness_badge = "secondary"
        elif state_code == "STATE_3_CAREER_MATCH":
            if match_pct >= 75:
                readiness = "Strong Career Match"
                readiness_badge = "primary"
            elif match_pct >= 55:
                readiness = "Good Career Match"
                readiness_badge = "primary"
            elif match_pct >= 35:
                readiness = "Developing Match"
                readiness_badge = "warning"
            else:
                readiness = "Exploratory Match"
                readiness_badge = "secondary"
        else: # STATE_4_VERIFIED
            if match_pct >= 80:
                readiness = "Role Ready"
                readiness_badge = "success"
            elif match_pct >= 65:
                readiness = "Verified Near Ready"
                readiness_badge = "success"
            elif match_pct >= 45:
                readiness = "Developing Competency"
                readiness_badge = "warning"
            else:
                readiness = "Early Exploration"
                readiness_badge = "secondary"

        # Generate Explainable AI reasoning based on current progressive state
        top_verified = [s for s, v in verified_skill_map.items() if s.lower() in [cs.lower() for cs in core_skills]]
        detected_matching = [s for s in core_skills if s.lower() in extracted_lower]

        if state_code == "STATE_2_PRELIMINARY":
            if detected_matching:
                reason = f"Preliminary match based solely on {len(detected_matching)} detected skills from your resume ({', '.join(detected_matching[:3])}). Complete the overall assessment and technical skill tests to verify readiness."
            else:
                reason = "No matching skills identified for this track from your resume. Complete assessments to evaluate aptitude."
        elif state_code == "STATE_3_CAREER_MATCH":
            parts = []
            if detected_matching:
                parts.append(f"detected resume skills ({', '.join(detected_matching[:3])})")
            if domain_avg > 0:
                parts.append(f"{domain_avg:.0f}% domain alignment across {', '.join(ideal_domains)}")
            reason = f"Career match derived from {' and '.join(parts)}. Complete technical tests to achieve verified readiness."
        else: # STATE_4_VERIFIED
            parts = []
            if top_verified:
                parts.append(f"verified proficiency in {', '.join(top_verified[:3])}")
            elif detected_matching:
                parts.append(f"claimed skills in {', '.join(detected_matching[:3])}")
            if domain_avg > 0:
                parts.append(f"strong domain alignment in {', '.join(ideal_domains)}")
            if missing_skills:
                parts.append(f"bridging {', '.join(missing_skills[:2])} will finalize role readiness")
            reason = " & ".join(parts).capitalize() if parts else "Verified competency evaluated across technical testing and domain metrics."

        results.append({
            "name": role_name,
            "category": config["category"],
            "icon": config["icon"],
            "description": config["description"],
            "match": match_pct,
            "readiness": readiness,
            "readiness_badge": readiness_badge,
            "state_label": state_label,
            "state_code": state_code,
            "matching_skills": matched_skills if matched_skills else detected_matching,
            "needs_improvement": needs_improvement_skills,
            "missing_skills": missing_skills,
            "core_skills": core_skills,
            "reason": reason,
            "is_target": bool(preferred_career and preferred_career.lower() == role_name.lower())
        })

    # Sort descending by match percentage
    results.sort(key=lambda x: x["match"], reverse=True)
    return results


def perform_skill_gap_analysis(selected_career_name, extracted_skills, verified_skill_map):
    """
    Performs detailed 3-tier gap analysis for a specifically chosen career target:
    - Already Have (Verified Advanced/Expert)
    - Needs Improvement (Verified Intermediate or Unverified Claimed)
    - Missing Skills (Not yet acquired)
    """
    config = CAREER_CATALOG.get(selected_career_name)
    if not config:
        # Fallback to Data Analyst if invalid
        selected_career_name = "Data Analyst"
        config = CAREER_CATALOG["Data Analyst"]

    core_skills = config["core_skills"]
    extracted_lower = {s.lower() for s in extracted_skills}
    verified_lower = {k.lower(): v for k, v in verified_skill_map.items()}

    already_have = []
    needs_improvement = []
    missing = []

    for s in core_skills:
        s_low = s.lower()
        if s_low in verified_lower:
            ver = verified_lower[s_low]
            if ver.get("score", 0) >= 70:
                already_have.append({
                    "skill": s,
                    "level": ver.get("level", "Advanced"),
                    "score": ver.get("score", 0),
                    "status": "Verified Proficient"
                })
            else:
                needs_improvement.append({
                    "skill": s,
                    "level": ver.get("level", "Intermediate"),
                    "score": ver.get("score", 0),
                    "status": "Assessed (Needs Practice)"
                })
        elif s_low in extracted_lower:
            needs_improvement.append({
                "skill": s,
                "level": "Unverified",
                "score": 0,
                "status": "Claimed in Resume"
            })
        else:
            missing.append({
                "skill": s,
                "status": "Missing Essential Skill"
            })

    total = len(core_skills)
    have_count = len(already_have)
    partial_count = len(needs_improvement)
    
    # Career readiness index
    readiness_pct = round(((have_count * 1.0 + partial_count * 0.5) / max(total, 1)) * 100)

    return {
        "career_name": selected_career_name,
        "description": config["description"],
        "readiness_pct": readiness_pct,
        "already_have": already_have,
        "needs_improvement": needs_improvement,
        "missing": missing,
        "total_required": total
    }
