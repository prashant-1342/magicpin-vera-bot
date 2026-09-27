"""
Composer module for generating high-specificity, category-aligned,
and merchant-personalized messages across all domain trigger types.
"""

from typing import Dict, Any, Optional, Tuple, List


def get_greeting(category_slug: str, owner_name: str, languages: list) -> str:
    """Format appropriate professional greeting honoring category honorifics."""
    if category_slug == "dentists":
        name = f"Dr. {owner_name}" if owner_name and not owner_name.startswith("Dr.") else (owner_name or "Doctor")
        return f"Hello {name}"
    
    if owner_name:
        return f"Hi {owner_name}"
    return "Hi there"


def get_audience_term(category_slug: str) -> str:
    """Category-specific terminology for patrons/customers."""
    terms = {
        "dentists": "patients",
        "salons": "clients",
        "restaurants": "diners",
        "gyms": "members",
        "pharmacies": "customers"
    }
    return terms.get(category_slug, "customers")


def find_digest_item(category: Dict[str, Any], item_id: str) -> Optional[Dict[str, Any]]:
    """Look up research digest item from category context."""
    for item in category.get("digest", []):
        if item.get("id") == item_id:
            return item
    return None


def compose_message(
    category: Dict[str, Any],
    merchant: Dict[str, Any],
    trigger: Dict[str, Any],
    customer: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, str, str]:
    """
    Compose high-specificity message based on category, merchant, trigger, and optional customer.
    Returns: (body, cta, suppression_key, rationale)
    """
    cat_slug = category.get("slug", merchant.get("category_slug", "generic"))
    m_identity = merchant.get("identity", {})
    owner_name = m_identity.get("owner_first_name", "")
    merchant_name = m_identity.get("name", "your business")
    locality = m_identity.get("locality", "your area")
    city = m_identity.get("city", "")
    languages = m_identity.get("languages", ["en"])
    m_id = merchant.get("merchant_id", "unknown_m")
    
    greeting = get_greeting(cat_slug, owner_name, languages)
    audience = get_audience_term(cat_slug)
    
    # Select best active offer or fallback catalog offer
    offers = merchant.get("offers", [])
    active_offers = [o for o in offers if o.get("status") == "active"]
    if active_offers:
        primary_offer = active_offers[0]
    elif offers:
        primary_offer = offers[0]
    else:
        cat_offers = category.get("offer_catalog", [])
        primary_offer = cat_offers[0] if cat_offers else {"title": "special offer", "price_inr": 0, "value": "0"}

    offer_title = primary_offer.get("title", "special service")
    offer_price = primary_offer.get("price_inr") or primary_offer.get("value")
    try:
        offer_price = int(offer_price) if offer_price is not None else 0
    except (ValueError, TypeError):
        offer_price = 0
        
    price_str = f"₹{offer_price:,} " if offer_price and offer_price > 0 else ""
    
    kind = trigger.get("kind", "general_update")
    payload = trigger.get("payload", {})
    t_id = trigger.get("id", "trig_000")
    
    # 1. Research Digest
    if kind == "research_digest":
        top_item_id = payload.get("top_item_id", "")
        digest_item = find_digest_item(category, top_item_id)
        if digest_item:
            source = digest_item.get("source", "industry research")
            title = digest_item.get("title", "clinical study")
            trial_n = digest_item.get("trial_n")
            trial_text = f" (trial of {trial_n:,} patients)" if trial_n else ""
            summary = digest_item.get("summary", "")
            if cat_slug == "dentists":
                body = (
                    f"{greeting}, {source}{trial_text}: '{title}'. "
                    f"{summary} Recovering overdue preventative visits captures unbooked chairside appointments in {locality}. "
                    f"Want me to launch a recall invite with your {price_str}{offer_title} for eligible {audience}?"
                )
            elif cat_slug == "gyms":
                body = (
                    f"{greeting}, {source}{trial_text}: '{title}'. "
                    f"{summary} Re-engaging at-risk {audience} prevents member drop-off and fills underutilized slots in {locality}. "
                    f"Want me to send your {price_str}{offer_title} offer to active searchers?"
                )
            elif cat_slug == "salons":
                body = (
                    f"{greeting}, {source}{trial_text}: '{title}'. "
                    f"{summary} Filling weekday gaps captures high-margin chair appointments across {locality}. "
                    f"Shall I send your {price_str}{offer_title} offer to nearby {audience}?"
                )
            elif cat_slug == "restaurants":
                body = (
                    f"{greeting}, {source}{trial_text}: '{title}'. "
                    f"{summary} Driving off-peak table bookings maximizes cover revenue in {locality}. "
                    f"Want me to spotlight your {price_str}{offer_title} offer to nearby {audience}?"
                )
            elif cat_slug == "pharmacies":
                body = (
                    f"{greeting}, {source}{trial_text}: '{title}'. "
                    f"{summary} Improving refill adherence ensures recurring monthly prescription volume in {locality}. "
                    f"Shall I dispatch a 1-tap reorder reminder for your {price_str}{offer_title}?"
                )
            else:
                body = (
                    f"{greeting}, {source}{trial_text}: '{title}'. "
                    f"{summary} Recover missed revenue by reaching active {audience} in {locality}. "
                    f"Want me to set up a campaign with your {price_str}{offer_title}?"
                )
            rationale = f"Cited published research from {source} regarding '{title}'."
        else:
            topic = payload.get("topic", "clinical research")
            body = (
                f"{greeting}, new research update for {cat_slug} in {locality}: '{topic}'. "
                f"Want me to set up a recall campaign with your {price_str}{offer_title} for affected {audience}?"
            )
            rationale = f"Research digest update on {topic}."
        cta = "review_research_summary"
        suppression_key = f"{m_id}:research_digest:{top_item_id or 'general'}"

    # 2. Regulation / Compliance Change
    elif kind in ("regulation_change", "compliance_alert"):
        deadline = payload.get("deadline_iso", "2026-12-15")
        item_id = payload.get("top_item_id", "regulation")
        digest_item = find_digest_item(category, item_id)
        reg_title = digest_item.get("title", "revised regulatory standards") if digest_item else "revised compliance guidelines"
        body = (
            f"Compliance notice: '{reg_title}' is effective from {deadline}. "
            f"Would you like me to generate a quick compliance checklist for {merchant_name}?"
        )
        cta = "view_compliance_checklist"
        suppression_key = f"{m_id}:compliance:{deadline}"
        rationale = f"Upcoming regulatory deadline ({deadline}) for {reg_title}."

    # 3. Customer Recall Due
    elif kind == "recall_due":
        cust_name = customer.get("identity", {}).get("name", "Your patient") if customer else "A regular patient"
        service_due = payload.get("service_due", "routine checkup").replace("_", " ")
        due_date = payload.get("due_date", "this week")
        slots = payload.get("available_slots", [])
        slot_text = f" (open slot: {slots[0].get('label')})" if slots else ""
        body = (
            f"{cust_name} is due for their {service_due} on {due_date}{slot_text}. "
            f"Should I send them a booking reminder with available slots?"
        )
        cta = "send_recall_reminder"
        suppression_key = f"{m_id}:recall:{customer.get('customer_id') if customer else 'generic'}"
        rationale = f"Scheduled recall due on {due_date} for {cust_name}."

    # 4. Performance Dip / Seasonal Dip
    elif kind in ("perf_dip", "performance_dip", "seasonal_perf_dip"):
        metric = payload.get("metric", "views")
        delta_pct = payload.get("delta_pct", -0.25)
        pct_display = abs(int(delta_pct * 100)) if isinstance(delta_pct, float) else str(delta_pct).replace("-", "")
        baseline = payload.get("vs_baseline", 15)
        window = payload.get("window", "7d")
        body = (
            f"Your {metric} in {locality} saw a {pct_display}% dip over the last {window} (vs baseline of {baseline}). "
            f"Want me to spotlight your {price_str}{offer_title} offer to bring in more {audience}?"
        )
        cta = "boost_merchant_visibility"
        suppression_key = f"{m_id}:perf_dip:{metric}"
        rationale = f"{pct_display}% drop in {metric} over {window} vs baseline of {baseline}."

    # 5. Renewal Due / Subscription Expiry
    elif kind == "renewal_due":
        days = payload.get("days_remaining", 14)
        plan = payload.get("plan", "Pro")
        amt = payload.get("renewal_amount", 4999)
        body = (
            f"Your {plan} plan for {merchant_name} expires in {days} days (renewal: ₹{amt:,}). "
            f"Would you like me to generate your renewal link to keep campaigns running?"
        )
        cta = "renew_subscription"
        suppression_key = f"{m_id}:renewal:{days}d"
        rationale = f"Subscription expiring in {days} days on {plan} plan."

    # 6. Festival Upcoming / Event
    elif kind in ("festival_upcoming", "festival_event", "seasonal_event"):
        festival = payload.get("festival", payload.get("event_name", "Festive Season"))
        days_until = payload.get("days_until")
        days_text = f" in {days_until} days" if days_until else ""
        body = (
            f"{festival} is coming up{days_text}! Searches in {locality} are projected to rise. "
            f"Shall I prepare your {price_str}{offer_title} festival campaign draft?"
        )
        cta = "prepare_festival_draft"
        suppression_key = f"{m_id}:festival:{festival.lower().replace(' ', '_')}"
        rationale = f"Upcoming festival ({festival}) driving seasonal local demand."

    # 7. Wedding / Bridal Follow-up
    elif kind in ("wedding_package_followup", "bridal_followup"):
        cust_name = customer.get("identity", {}).get("name", "Your client") if customer else "A bridal client"
        wedding_date = payload.get("wedding_date", "in November")
        days_to = payload.get("days_to_wedding", 180)
        next_step = payload.get("next_step_window_open", "skin prep program").replace("_", " ")
        body = (
            f"{cust_name}'s wedding is on {wedding_date} ({days_to} days away). Time for the {next_step}. "
            f"Should I send her the schedule to book her session?"
        )
        cta = "send_bridal_schedule"
        suppression_key = f"{m_id}:bridal_followup:{customer.get('customer_id') if customer else 'generic'}"
        rationale = f"Bridal timeline milestone ({days_to} days to wedding) for {cust_name}."

    # 8. IPL Match Today
    elif kind == "ipl_match_today":
        match = payload.get("match", "today's match")
        venue = payload.get("venue", "the stadium")
        match_time = payload.get("match_time_iso", "19:30")
        time_display = "7:30 PM" if "19:30" in str(match_time) else "match time"
        body = (
            f"IPL Match Alert: {match} is playing at {venue} tonight at {time_display}. "
            f"Want me to send a match-night {price_str}{offer_title} special to nearby {audience}?"
        )
        cta = "launch_match_special"
        suppression_key = f"{m_id}:ipl:{match.lower().replace(' ', '_')}"
        rationale = f"Live IPL match demand spike for {match} at {venue}."

    # 9. Review Theme Emerged
    elif kind in ("review_theme_emerged", "review_alert"):
        theme = payload.get("theme", "service speed").replace("_", " ")
        occurrences = payload.get("occurrences_30d", 3)
        quote = payload.get("common_quote", "good service")
        body = (
            f"Review alert: {occurrences} recent reviews in 30 days mentioned '{theme}' (e.g. \"{quote}\"). "
            f"Should I draft a quick response template for your team?"
        )
        cta = "review_feedback_template"
        suppression_key = f"{m_id}:review_theme:{theme.lower().replace(' ', '_')}"
        rationale = f"{occurrences} review mentions on theme '{theme}'."

    # 10. Milestone Reached
    elif kind == "milestone_reached":
        metric = payload.get("metric", "reviews").replace("_", " ")
        val_now = payload.get("value_now", 145)
        milestone = payload.get("milestone_value", 150)
        diff = milestone - val_now if milestone > val_now else 5
        body = (
            f"Milestone alert: {merchant_name} has {val_now} {metric}, just {diff} away from {milestone}! "
            f"Want me to invite recent happy {audience} to leave a review and hit {milestone}?"
        )
        cta = "request_milestone_reviews"
        suppression_key = f"{m_id}:milestone:{milestone}"
        rationale = f"Only {diff} {metric} needed to reach {milestone} milestone."

    # 11. Active Planning Intent
    elif kind == "active_planning_intent":
        topic = payload.get("intent_topic", "bulk packages").replace("_", " ")
        last_msg = payload.get("merchant_last_message", "tell me more")
        body = (
            f"Following up on our discussion regarding '{topic}' (you noted: \"{last_msg}\"). "
            f"Here is the package outline for {price_str}{offer_title}. Ready for me to activate the draft?"
        )
        cta = "confirm_planning_package"
        suppression_key = f"{m_id}:planning:{topic.lower().replace(' ', '_')}"
        rationale = f"Following up on merchant's active planning intent for {topic}."

    # 12. Chronic Medicine Refill Due
    elif kind in ("chronic_refill_due", "medicine_refill_due"):
        cust_name = customer.get("identity", {}).get("name", "A patient") if customer else "A chronic patient"
        med = payload.get("medicine", "regular prescription")
        body = (
            f"{cust_name} is due for their monthly {med} prescription refill this week. "
            f"Should I send a quick 1-tap WhatsApp reorder link to them?"
        )
        cta = "send_refill_link"
        suppression_key = f"{m_id}:refill:{customer.get('customer_id') if customer else 'generic'}"
        rationale = f"Chronic prescription refill due for {cust_name}."

    # 13. Appointment Tomorrow
    elif kind == "appointment_tomorrow":
        cust_name = customer.get("identity", {}).get("name", "A client") if customer else "Your client"
        time_slot = payload.get("time", "tomorrow")
        service = payload.get("service", "scheduled service")
        body = (
            f"Reminder: {cust_name} has an appointment for {service} at {time_slot}. "
            f"Should I dispatch the automated confirmation and directions link?"
        )
        cta = "send_appointment_reminder"
        suppression_key = f"{m_id}:app_reminder:{customer.get('customer_id') if customer else 'generic'}"
        rationale = f"Upcoming appointment tomorrow at {time_slot} for {cust_name}."

    # 14. Trial Follow-up
    elif kind == "trial_followup":
        cust_name = customer.get("identity", {}).get("name", "A trial visitor") if customer else "A trial member"
        body = (
            f"{cust_name} just completed their trial pass. "
            f"Should I send them your {price_str}{offer_title} membership offer to convert them?"
        )
        cta = "convert_trial_member"
        suppression_key = f"{m_id}:trial_followup:{customer.get('customer_id') if customer else 'generic'}"
        rationale = f"Follow-up for {cust_name} post trial session."

    # 15. Winback Eligible
    elif kind == "winback_eligible":
        days_exp = payload.get("days_since_expiry", 30)
        lapsed = payload.get("lapsed_customers_added_since_expiry", 20)
        body = (
            f"Since subscription paused {days_exp} days ago, {lapsed} past {audience} became inactive in {locality}. "
            f"Shall I reactivate your {price_str}{offer_title} to win them back?"
        )
        cta = "reactivate_account"
        suppression_key = f"{m_id}:winback:{days_exp}d"
        rationale = f"Winback opportunity for account inactive {days_exp}d with {lapsed} lapsed users."

    # 16. Curious Ask Due
    elif kind == "curious_ask_due":
        body = (
            f"Quick question for {merchant_name}: Which service or slot is seeing the highest demand in {locality} this week? "
            f"Reply with the service name and I'll create a promotional draft instantly."
        )
        cta = "share_demand_update"
        suppression_key = f"{m_id}:curious_ask"
        rationale = "Low-friction merchant check-in on weekly service trends."

    # 17. Competitor Opened / Competitor Surge
    elif kind in ("competitor_opened", "competitor_surge"):
        comp_name = payload.get("competitor_name", "A new competitor")
        dist = payload.get("distance", "within 2 km")
        body = (
            f"{comp_name} recently opened in {locality} ({dist}). "
            f"Want me to highlight your {price_str}{offer_title} to protect your local market share?"
        )
        cta = "counter_competitor"
        suppression_key = f"{m_id}:competitor:{locality.lower().replace(' ', '_')}"
        rationale = f"Competitive pressure from {comp_name} in {locality}."

    # 18. Research / Search Spike (Standard)
    elif kind in ("research_spike", "search_spike"):
        query = payload.get("search_query", "your services")
        count = payload.get("search_count_nearby", 190)
        timeframe = payload.get("timeframe", "the past 48 hours")
        body = (
            f"{count} people in {locality} searched for '{query}' in {timeframe}. "
            f"Want me to send them your {price_str}{offer_title} offer?"
        )
        cta = "send_search_spike_offer"
        suppression_key = f"{m_id}:search_spike:{query.lower().replace(' ', '_')}"
        rationale = f"High local search volume ({count} searches for '{query}') in {locality}."

    # Default fallback
    else:
        body = (
            f"Local searches in {locality} are trending up this week. "
            f"Would you like me to feature your {price_str}{offer_title} offer to nearby {audience}?"
        )
        cta = "promote_active_offer"
        suppression_key = f"{m_id}:general_nudge"
        rationale = f"Locality traffic growth in {locality}."

    return body, cta, suppression_key, rationale
