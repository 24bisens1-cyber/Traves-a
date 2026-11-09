# TRAVESÍA — Provider Onboarding and Approval Plan

**Status date:** 6 November 2026  
**Product name:** TRAVESÍA — The World Is Yours to Explore.

This document separates what TRAVESÍA can operate today from commercial/provider approvals that must be issued to the legal operator by the provider. It does not claim that TRAVESÍA has been approved as an IRCTC Principal Service Provider, an IRCTC affiliate, an Amadeus production booking client, or an airline ticket issuer.

## 1. What works today without private booking credentials

- Flight discovery: route-aware Google Flights and KAYAK searches plus ixigo Flights as a no-key provider hand-off. The prices, inventory and checkout are supplied by those external sites.
- Indian rail: official IRCTC and ixigo train search/checkout hand-offs. The current IRCTC authorised B2C provider list includes Le Travenues Technology Ltd. (ixigo) as a B2C Principal Service Provider.
- Fare comparison: TRAVESÍA compares user-entered totals and journey durations. It does not invent prices or seat availability.
- Provider status: `/api/providers/status` now returns the exact production prerequisites and the recommended rail affiliate route.

Official sources:
- IRCTC authorised provider list (March 2026): https://contents.irctc.co.in/en/IRCTC%20Authorised%20Principal%20Service%20Providers.pdf
- IRCTC B2C PSP policy document: https://contents.irctc.co.in/en/New_B2C_Policy.pdf
- Amadeus production application and ticket-issuance requirements: https://github.com/amadeus4dev/developer-guides/blob/master/docs/API-Keys/moving-to-production.md
- Amadeus Self-Service FAQ: https://admin.developers.amadeus.com/self-service/apis-docs/guides/developer-guides/faq/

## 2. Recommended railway route: affiliate/associate of an existing B2C PSP

IRCTC's published B2C policy includes an affiliate/associate arrangement. Under that route, an existing B2C PSP can register a third-party firm/startup/MSME as its affiliate or associate so the third party's website/mobile app can expose that PSP's rail search and booking workflow. The affiliate does not become an independent IRCTC PSP merely by linking to the PSP.

### Suggested partner target

Le Travenues Technology Ltd. (ixigo) is listed in IRCTC's March 2026 authorised B2C PSP list. TRAVESÍA already links to ixigo's train search and should ask ixigo whether it will onboard TRAVESÍA under its current affiliate/associate programme and provide an approved integration option (web hand-off, deep link, widget, SDK or API, as permitted by its current agreement).

This is a partner request, not a guarantee of acceptance or API access. IRCTC's policy says the B2C PSP must request/register the affiliate/associate with IRCTC.

### Documents to prepare

The published IRCTC policy lists the following affiliate/associate documentation:

1. Self-attested certificate of incorporation/registration or other document supporting the entity's registration in India.
2. For a startup: self-attested DPIIT startup-recognition certificate and a CA certificate of previous-year turnover.
3. For an MSME: self-attested MSME recognition certificate.
4. Self-attested previous-year balance sheet and Income Tax Return, together with PAN details.
5. Product background, operating model, technical architecture, support contact and the intended website/mobile app URL. These additional materials help the B2C PSP assess the proposed integration; they do not replace IRCTC's stated documents.

The policy document's affiliate/associate fee table lists the following fees for a **mobile-app affiliate registration**: ₹3 lakh + applicable taxes for 3 months, ₹5 lakh + taxes for 6 months, ₹7 lakh + taxes for 9 months, or ₹10 lakh + taxes for 1 year. The document says the B2C PSP pays the registration fee to IRCTC. The commercial agreement may determine whether/how any cost is passed to the affiliate. **The published policy PDF is an older policy edition/addendum; request the current fee schedule and written confirmation from IRCTC and the chosen PSP before making any commitment or payment.**

### Execution sequence

1. Choose the current IRCTC-listed B2C PSP (ixigo is the first suggested contact, not a confirmed partner).
2. Ask its partnerships/business-development team for its current affiliate/associate onboarding route for an independent travel-planning web app.
3. Ask whether it supports search-only, deep links, widgets, SDK/API or white-label booking, and which options are permitted by its IRCTC agreement.
4. Ask for current fees, transaction charges, settlement model, refund/cancellation ownership, data-sharing terms, branding rules, minimum volumes and technical documentation in writing.
5. Provide only the documents requested through the PSP's official secure channel.
6. The PSP submits the affiliate/associate registration request to IRCTC and obtains registration/approval. Do not enable an in-app booking claim until written approval and test credentials/integration access are received.
7. Integrate the approved method server-side or as a provider-owned hand-off. Keep provider credentials server-side; never collect or proxy IRCTC passwords or payment-card data.
8. Run partner UAT, refund/cancellation cases, failed-payment cases, and confirmation/PNR reconciliation before production launch.

## 3. Alternative railway route: direct B2C PSP registration

Direct B2C PSP registration is a much heavier commercial route. IRCTC's published policy describes a registered Indian private company, proprietorship, partnership or LLP and requires supporting documents. For the website/bouquet options, it states a previous-year turnover of ₹5 crore and two prior years' balance sheets and ITRs. It also asks for the firm's technical-expertise background.

For the mobile-app-only platform, the policy lists a one-time non-refundable integration charge of ₹10 lakh + taxes, minimum annual maintenance charges of ₹5 lakh + taxes, and a refundable ₹10 lakh security deposit. It also describes a rolling-deposit account (minimum balance ₹1 lakh) and requires the PSP to have its own customer payment system. The exact policy and commercials must be confirmed directly with IRCTC before any action because the PDF is an older edition/addendum.

This route is not necessary to keep TRAVESÍA useful: the existing IRCTC and approved-provider hand-offs remain operational while an affiliate relationship is considered.

## 4. Flight search and ticket issuance: Amadeus

### Flight-offer search

1. Create an Amadeus for Developers account and a TRAVESÍA application in the Self-Service workspace.
2. Create the API key/secret and store them only in the server environment as `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET`.
3. Start with `AMADEUS_BASE_URL=https://test.api.amadeus.com`. Test-environment results are labelled as test responses, not live inventory.
4. Request production access in the Amadeus workspace. Amadeus's guide says to complete the app/contact/billing details, indicate required APIs, choose payment terms and sign the supplied terms. Production approval is issued by Amadeus; it cannot be self-granted by TRAVESÍA.
5. Change the base URL to `https://api.amadeus.com` only after production access is approved.

### Actual ticket issuance

Amadeus Flight Offers Search is not ticket issuance. For Self-Service Flight Create Orders in production, Amadeus requires a ticket-issuance agreement with an airline consolidator unless the operator is independently accredited to issue tickets. The consolidator receives the PNR and issues the ticket under its agreement. The consolidator also controls post-booking changes/refunds under its contract. TRAVESÍA has no ticketing agreement configured in this release.

The Amadeus documentation states that Self-Service ticket issuance is not available in every country; India is not in the restricted-country list shown in its production guide at the time this document was prepared. That does not waive the consolidator contract or local compliance requirements.

## 5. Partner request draft

Use this as a draft for an official partner form or email; do not send it until the legal operator details and recipient are confirmed.

**Subject:** Affiliate/associate integration enquiry — TRAVESÍA travel-planning platform

Hello Partnerships Team,

We are developing TRAVESÍA, a travel-planning web application that helps users discover destinations, plan group trips, compare transport options and manage shared trip expenses. We would like to understand your current affiliate/associate onboarding process for an Indian web application and whether your approved rail-booking experience can be integrated through a partner-approved deep link, widget, SDK, API or white-label flow.

Please share the current eligibility and registration documents, commercial/registration fees, settlement and refund responsibilities, permitted branding, technical documentation, sandbox/UAT process and the steps required for IRCTC affiliate/associate registration.

We will provide the registered entity details, PAN, applicable DPIIT/MSME documents, CA-certified turnover and financial records through your approved secure channel once the eligibility route is confirmed.

Regards,  
TRAVESÍA Project Team

## 6. What remains a provider-side gate

| Capability | TRAVESÍA implementation | External gate |
|---|---|---|
| Globe and trip tools | Included; no provider key required for fallback renderer | None for local operation |
| Flight search hand-off | Included; route/date-aware no-key external searches | External sites control availability and prices |
| Amadeus in-app flight offers | Adapter and server-side credential support included | Owner's account, API key/secret and production approval |
| Amadeus ticket issuance | Not enabled | Production Flight Create Orders entitlement plus signed consolidator/issuer agreement |
| IRCTC/ixigo hand-off | Included | None for provider-site checkout |
| TRAVESÍA in-app rail booking | Not enabled | Written PSP/affiliate agreement, IRCTC registration, partner technical access and UAT |

TRAVESÍA must not claim to be an IRCTC authorised agent, PSP, airline consolidator, ticket issuer or booking intermediary until the relevant written approval/contract is actually issued to the operating legal entity.
