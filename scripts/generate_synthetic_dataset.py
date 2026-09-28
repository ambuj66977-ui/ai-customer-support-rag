"""Generate the deterministic synthetic FAQ pilot dataset.

The fictional company and its policies exist only for this portfolio project.
The generated CSV is raw input; downstream preprocessing must not edit it.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "raw" / "customer_support_synthetic.csv"


def _faq(category: str, intent: str, question: str, answer: str) -> dict[str, str]:
    return {
        "category": category,
        "intent": intent,
        "question": question,
        "answer": answer,
    }


FAQ_RECORDS = [
    # Account
    _faq("account", "create_account", "How do I create a Northstar Shop account?", "Select Create account, enter your email address, create a password, and verify the email we send you."),
    _faq("account", "close_account", "Can I permanently close my account?", "Yes. Open Settings, select Privacy, choose Close account, and confirm the request. Pending orders must be completed first."),
    _faq("account", "change_email", "Where can I change the email on my account?", "Open Settings, select Contact details, enter the new email address, and verify it using the confirmation message."),
    _faq("account", "change_phone", "How can I update my phone number?", "Go to Settings, open Contact details, replace the phone number, and complete the verification code step."),
    _faq("account", "account_verification", "Why do I need to verify my account?", "Verification confirms that you control the registered email or phone number and helps protect the account from unauthorized use."),
    _faq("account", "multiple_accounts", "May I have more than one customer account?", "You may create another account with a different email address, but orders, rewards, and saved details cannot be combined automatically."),
    _faq("account", "reactivate_account", "Can a closed account be reactivated?", "A closed account cannot be reactivated. You can create a new account with the same email after the closure process is complete."),
    _faq("account", "guest_checkout", "Do I need an account to place an order?", "No. Guest checkout is available, although an account is required to view order history and collect reward points."),
    _faq("account", "download_account_data", "How can I download a copy of my account data?", "Open Settings, select Privacy, and choose Request data export. A download link is emailed after the export is prepared."),
    _faq("account", "merge_accounts", "Can support merge two accounts for me?", "Accounts cannot be merged. Support can help you choose which account to keep, but orders and reward points remain on their original accounts."),

    # Authentication
    _faq("authentication", "forgot_password", "I forgot my password. How do I reset it?", "Select Forgot password on the sign-in page and follow the reset link sent to your registered email address."),
    _faq("authentication", "reset_link_expired", "My password reset link has expired. What should I do?", "Request a new reset link from the sign-in page. For security, only the most recently issued link will work."),
    _faq("authentication", "locked_account", "Why is my account temporarily locked?", "Several unsuccessful sign-in attempts can trigger a 30-minute lock. Wait for the lock to expire or reset your password."),
    _faq("authentication", "enable_two_factor", "How do I turn on two-factor authentication?", "Open Settings, select Security, enable two-factor authentication, and connect an authenticator app using the displayed code."),
    _faq("authentication", "lost_two_factor_device", "I lost the phone used for two-factor authentication.", "Use a saved recovery code to sign in. If none is available, contact support and complete account-ownership verification."),
    _faq("authentication", "sign_out_all_devices", "Can I sign out of every device at once?", "Yes. Go to Settings, select Security, and choose Sign out all devices. Your current session will also end."),
    _faq("authentication", "unknown_login_alert", "I received a login alert that I do not recognize.", "Change your password immediately, sign out all devices, enable two-factor authentication, and contact support if account details were changed."),
    _faq("authentication", "verification_code_missing", "Why has my sign-in verification code not arrived?", "Check the registered email or phone number, wait a few minutes, inspect spam folders, and then request one new code."),
    _faq("authentication", "social_login", "Can I sign in with a social media account?", "Northstar Shop currently supports email-and-password sign-in only; social sign-in is not available."),
    _faq("authentication", "password_requirements", "What are the password requirements?", "Passwords must contain at least 12 characters, including an uppercase letter, a lowercase letter, a number, and a symbol."),

    # Profile and addresses
    _faq("profile", "edit_name", "How do I correct the name on my profile?", "Open Settings, select Personal details, update your name, and save. Contact support if an order already has the wrong name."),
    _faq("profile", "add_address", "How can I add a new delivery address?", "Open Address book, select Add address, enter the delivery details, and save them."),
    _faq("profile", "edit_address", "Where can I edit a saved address?", "Open Address book, select the saved address, choose Edit, update the details, and save."),
    _faq("profile", "delete_address", "How do I remove an old address?", "Open Address book, select the address, and choose Delete. An address attached to an active order cannot be removed from that order."),
    _faq("profile", "default_address", "Can I choose a default shipping address?", "Yes. Open Address book and select Set as default beside the address you want preselected at checkout."),
    _faq("profile", "billing_address", "How do I update my billing address?", "Edit the billing address during checkout or update it under Payment methods. Existing completed orders will not change."),
    _faq("profile", "address_after_order", "Can I change the address after placing an order?", "You can request an address correction before packing begins. Once shipped, contact the carrier; rerouting is not guaranteed."),
    _faq("profile", "profile_photo", "Can I add a profile photo?", "Profile photos are not currently supported on Northstar Shop accounts."),
    _faq("profile", "language_preference", "How do I change my preferred language?", "Open Settings, select Preferences, choose an available language, and save the change."),
    _faq("profile", "communication_preferences", "Where can I manage marketing messages?", "Open Settings, select Communications, and update your email and text-message preferences. Transactional order messages remain enabled."),

    # Billing
    _faq("billing", "invoice_download", "Where can I download an invoice?", "Open Order history, select the completed order, and choose Download invoice."),
    _faq("billing", "invoice_name", "Can the name on an invoice be changed?", "Invoice details can be corrected before an order ships. After shipment, contact support to check whether a corrected invoice is permitted."),
    _faq("billing", "tax_calculation", "How is sales tax calculated?", "Applicable tax is calculated during checkout using the items, delivery address, and current local tax rules."),
    _faq("billing", "tax_exemption", "Does Northstar Shop support tax-exempt purchases?", "Eligible organizations can submit a valid exemption certificate to support before ordering. Approval is not retroactive."),
    _faq("billing", "duplicate_charge", "Why do I see two charges for one order?", "One entry may be a temporary authorization. If both charges settle, contact support with the order number and transaction dates."),
    _faq("billing", "pending_charge", "What does a pending card charge mean?", "A pending charge is an authorization placed by your bank. It normally disappears or becomes a completed charge within seven business days."),
    _faq("billing", "price_changed", "Why did the price change before I checked out?", "Prices and promotions are confirmed at checkout. Items left in a cart are not reserved at an earlier price."),
    _faq("billing", "currency", "Which currency will I be charged in?", "The checkout page displays the transaction currency before payment. Your bank may add conversion or international fees."),
    _faq("billing", "billing_error", "My billing address is being rejected.", "Enter the address exactly as it appears on your payment account, including postal code. Contact your bank if it is still rejected."),
    _faq("billing", "receipt_email", "Can you resend my purchase receipt?", "Open the order in Order history and select Resend receipt. Guest customers can use the link in their order-confirmation email."),

    # Payments
    _faq("payments", "accepted_methods", "What payment methods do you accept?", "Northstar Shop accepts major credit and debit cards plus any digital wallets displayed during checkout."),
    _faq("payments", "payment_declined", "Why was my card declined?", "Confirm the card details, billing address, available funds, and bank approval. Northstar Shop cannot override a bank decline."),
    _faq("payments", "change_payment_method", "Can I change payment after placing an order?", "The payment method cannot be changed on an existing order. Cancel the order before packing and place it again if cancellation is available."),
    _faq("payments", "saved_card", "How do I save a card for future orders?", "Select Save this payment method during checkout. Only tokenized payment details are stored, not the full card number."),
    _faq("payments", "remove_saved_card", "Where can I remove a saved card?", "Open Payment methods, select the saved card, and choose Remove."),
    _faq("payments", "split_payment", "Can I split an order between two cards?", "An order cannot be split across multiple bank cards. A gift card may be combined with one other accepted payment method."),
    _faq("payments", "cash_on_delivery", "Is cash on delivery available?", "Cash on delivery is not available. Payment must be completed through an option shown at checkout."),
    _faq("payments", "payment_retry", "How can I retry a failed payment?", "Return to checkout and submit the payment again or choose another available method. Verify that no successful order was created first."),
    _faq("payments", "card_security", "Is my card information secure?", "Payments are processed by a compliant payment provider, and Northstar Shop does not store full card numbers."),
    _faq("payments", "international_card", "Can I use a card issued in another country?", "International cards may work if the issuer permits the transaction and the billing information matches. Bank fees may apply."),

    # Orders
    _faq("orders", "order_status", "How can I check my order status?", "Sign in and open Order history, or use the tracking link in the confirmation email if you checked out as a guest."),
    _faq("orders", "order_confirmation_missing", "I did not receive an order-confirmation email.", "Check spam folders and confirm the email used at checkout. If payment succeeded but no order appears, contact support."),
    _faq("orders", "cancel_order", "Can I cancel my order?", "You can cancel from Order history until packing begins. After that point, wait for delivery and use the return process."),
    _faq("orders", "modify_order", "Can I add an item to an order I already placed?", "Items cannot be added to a submitted order. Place a separate order for additional products."),
    _faq("orders", "remove_item", "Can one item be removed from my order?", "Individual items cannot be removed after submission. If cancellation is still available, cancel and place a corrected order."),
    _faq("orders", "combine_orders", "Can two separate orders be combined?", "Separate orders cannot be combined after checkout and may ship or arrive independently."),
    _faq("orders", "guest_order", "How do I find an order placed as a guest?", "Use the order number and email address on the guest order lookup page, or follow the link in the confirmation email."),
    _faq("orders", "preorder", "How do preorders work?", "The product page shows the expected release date. Preorder items ship when available, and schedule changes are sent by email."),
    _faq("orders", "backorder", "What does backordered mean?", "A backordered item is temporarily unavailable but expected to return. The estimated dispatch window appears in your order details."),
    _faq("orders", "quantity_limit", "Why can I not order more units of an item?", "Some products have purchase limits because of stock availability, safety rules, or promotional conditions."),

    # Shipping
    _faq("shipping", "shipping_options", "Which shipping options are available?", "Available services, prices, and estimates are calculated from the delivery address and shown during checkout."),
    _faq("shipping", "shipping_cost", "How much will shipping cost?", "Shipping cost depends on destination, parcel size, and service level. The exact amount appears before payment."),
    _faq("shipping", "free_shipping", "When do I qualify for free shipping?", "Free standard shipping applies when the eligible merchandise subtotal reaches the threshold displayed at checkout."),
    _faq("shipping", "international_shipping", "Do you ship internationally?", "International delivery is available only to destinations listed at checkout. Duties and import taxes may be charged separately."),
    _faq("shipping", "po_box", "Can my order be delivered to a PO box?", "PO box delivery is available only when an eligible postal service appears at checkout; express courier services require a street address."),
    _faq("shipping", "dispatch_time", "How long does it take to dispatch an order?", "In-stock orders normally leave the warehouse within two business days. Preorders and personalized items take longer."),
    _faq("shipping", "weekend_shipping", "Are orders shipped on weekends?", "Warehouse dispatch occurs Monday through Friday, excluding public holidays. Some carriers may deliver on weekends."),
    _faq("shipping", "multiple_packages", "Why is my order arriving in multiple packages?", "Items may ship separately because they are stored in different locations or become available at different times."),
    _faq("shipping", "hazardous_items", "Why is expedited shipping unavailable for this product?", "Some batteries, liquids, and regulated items have carrier restrictions and can use only eligible ground services."),
    _faq("shipping", "delivery_estimate", "Is the delivery date guaranteed?", "Delivery dates are estimates unless checkout explicitly labels a service as guaranteed. Weather and carrier disruptions can cause delays."),

    # Delivery
    _faq("delivery", "track_package", "Where can I track my package?", "Open the shipped order and select Track package, or use the carrier link in the dispatch email."),
    _faq("delivery", "tracking_not_updated", "Why has tracking not updated?", "Carriers may take up to 48 hours to scan a newly shipped parcel. Contact support if there is still no update after that period."),
    _faq("delivery", "late_delivery", "My order is later than the estimated date.", "Check tracking for a carrier notice. If the estimate has passed by two business days, contact support for an investigation."),
    _faq("delivery", "marked_delivered_missing", "Tracking says delivered, but I cannot find the package.", "Check safe locations and ask household members or neighbors. If it remains missing after 24 hours, contact support."),
    _faq("delivery", "damaged_package", "The parcel arrived visibly damaged.", "Photograph the parcel and contents, keep the packaging, and contact support within seven days of delivery."),
    _faq("delivery", "failed_delivery", "What happens after a failed delivery attempt?", "The carrier may try again or hold the parcel at a collection point. Follow the instructions in the tracking record."),
    _faq("delivery", "delivery_instructions", "Can I add delivery instructions?", "Add supported instructions during checkout. Requests are passed to the carrier but cannot be guaranteed."),
    _faq("delivery", "signature_required", "Why does my delivery require a signature?", "High-value or restricted orders may require a signature to reduce loss and confirm delivery."),
    _faq("delivery", "wrong_item", "I received an item I did not order.", "Do not use the item. Contact support with the order number and a photo of the product label so a correction can be arranged."),
    _faq("delivery", "missing_item", "One item is missing from my delivery.", "Check whether the order was split into multiple shipments. If all packages arrived, contact support with the missing item details."),

    # Returns
    _faq("returns", "return_window", "How long do I have to return an item?", "Most unused items can be returned within 30 days of delivery. Final-sale and personalized products are excluded."),
    _faq("returns", "start_return", "How do I start a return?", "Open Order history, select the delivered order, choose Return items, and follow the instructions for eligible products."),
    _faq("returns", "return_shipping", "Who pays for return shipping?", "Northstar Shop covers return shipping for damaged or incorrect products. Other returns may have a label fee shown before confirmation."),
    _faq("returns", "return_condition", "What condition must a returned product be in?", "The item must be unused, complete, and in its original packaging unless it arrived damaged or defective."),
    _faq("returns", "final_sale", "Can final-sale products be returned?", "Final-sale products cannot be returned unless they arrive damaged, defective, or different from what was ordered."),
    _faq("returns", "personalized_return", "Can I return a personalized item?", "Personalized items are not returnable for preference changes, but support will help if the item is defective or made incorrectly."),
    _faq("returns", "return_multiple_items", "Can I return several items in one parcel?", "Yes, if the return instructions place them under the same return authorization. Do not combine items from unrelated returns."),
    _faq("returns", "return_without_account", "How do I return a guest order?", "Open the guest return page and enter the order number and checkout email to view eligible items and instructions."),
    _faq("returns", "return_label_missing", "I cannot find my return label.", "Reopen the return in Order history and download the label again. Some locations use a QR code instead of a printed label."),
    _faq("returns", "exchange", "Can I exchange an item for another size?", "Direct exchanges are not offered. Return the eligible item and place a new order for the preferred size."),

    # Refunds
    _faq("refunds", "refund_timing", "How long does a refund take?", "After the return is approved, refunds are sent to the original payment method within five business days; banks may take longer to post them."),
    _faq("refunds", "refund_method", "Can my refund go to a different card?", "Refunds must return to the original payment method. If that account is closed, ask the issuing bank how it handles incoming refunds."),
    _faq("refunds", "partial_refund", "Why was my refund smaller than the order total?", "Original express shipping, used gift value, return-label fees, or items not included in the return can reduce the refunded amount."),
    _faq("refunds", "refund_missing", "My approved refund has not appeared.", "Allow five business days plus your bank's posting time. Then contact support with the refund confirmation and order number."),
    _faq("refunds", "cancelled_order_refund", "When will I get money back for a cancelled order?", "A settled payment is refunded within five business days. A pending authorization may simply disappear according to your bank's timing."),
    _faq("refunds", "gift_card_refund", "How are gift-card purchases refunded?", "The amount paid by gift card returns to the same gift card, while any remainder returns to the other original payment method."),
    _faq("refunds", "shipping_refund", "Is the original delivery charge refundable?", "Standard delivery is refunded when the entire order is returned because it was faulty or incorrect. Optional express upgrades are not refunded."),
    _faq("refunds", "price_adjustment", "Can I get a refund if the price drops later?", "Northstar Shop does not provide post-purchase price adjustments. You may return an eligible item within the normal return window."),
    _faq("refunds", "refund_confirmation", "Will I receive confirmation when a refund is issued?", "Yes. A refund confirmation is emailed when the payment provider receives the refund instruction."),
    _faq("refunds", "cash_refund", "Can an online purchase be refunded in cash?", "No. Online refunds are returned through the original payment method and cannot be issued as cash."),

    # Subscriptions
    _faq("subscriptions", "start_subscription", "How do I start a product subscription?", "Choose an eligible product, select Subscribe, choose an available delivery frequency, and complete checkout."),
    _faq("subscriptions", "cancel_subscription", "Can I cancel my subscription?", "Open Subscriptions, select the plan, and choose Cancel before the next order begins processing."),
    _faq("subscriptions", "pause_subscription", "How can I pause upcoming subscription deliveries?", "Open the subscription and select Pause. Choose an available restart date before confirming."),
    _faq("subscriptions", "skip_delivery", "Can I skip only the next subscription shipment?", "Yes. Select Skip next delivery before its processing date; later deliveries remain scheduled."),
    _faq("subscriptions", "change_frequency", "How do I change how often my subscription arrives?", "Open the subscription, choose Delivery frequency, select an available interval, and save before processing begins."),
    _faq("subscriptions", "change_subscription_address", "Can I update the address for a subscription?", "Edit the delivery address from the subscription page before the next order starts processing."),
    _faq("subscriptions", "subscription_payment_failed", "What happens if a subscription payment fails?", "We email you and retry the payment once. Update the payment method before the retry to prevent the delivery from being skipped."),
    _faq("subscriptions", "subscription_price", "Will my subscription price always stay the same?", "Subscription prices can change. The current price and discount are shown before each recurring order is processed."),
    _faq("subscriptions", "subscription_discount", "How is the subscription discount applied?", "The eligible discount is applied automatically to each recurring order and appears in the order summary."),
    _faq("subscriptions", "subscription_item_unavailable", "What if my subscribed item is out of stock?", "That delivery is delayed or skipped, and we notify you by email. Other active subscriptions are unaffected."),

    # Products
    _faq("products", "product_availability", "How can I tell whether a product is in stock?", "The product page shows current availability. Stock is not reserved until checkout is completed."),
    _faq("products", "restock_notification", "Can you notify me when an item is back in stock?", "Select Notify me on the product page and enter your email. A notification does not reserve the item."),
    _faq("products", "product_dimensions", "Where can I find a product's dimensions?", "Dimensions and weight are listed under Specifications on the product page when supplied by the manufacturer."),
    _faq("products", "compatibility", "How do I check whether an accessory is compatible?", "Review the Compatibility section and match the exact model number. Contact support before ordering if your model is not listed."),
    _faq("products", "color_difference", "Why does the product color look different in person?", "Screens and lighting can affect color appearance. You may return an eligible unused item within the normal return window."),
    _faq("products", "manual", "Where can I download the product manual?", "If available, the manual appears under Downloads on the product page or in the manufacturer's support section."),
    _faq("products", "country_of_origin", "Where can I find a product's country of origin?", "Country-of-origin information appears in Specifications when available and is also printed on the product or packaging."),
    _faq("products", "age_restriction", "Why am I unable to buy an age-restricted product?", "Age-restricted products require eligibility confirmation and may be unavailable in some delivery locations."),
    _faq("products", "bundle_contents", "What is included in a product bundle?", "The Included in the box section lists every bundle component. Accessories not listed are sold separately."),
    _faq("products", "review_product", "How can I write a product review?", "After delivery, open the product from Order history and select Write a review. Reviews must follow the community guidelines."),

    # Warranty
    _faq("warranty", "warranty_length", "How long is the product warranty?", "The warranty period varies by product and is listed on the product page and purchase invoice."),
    _faq("warranty", "warranty_claim", "How do I make a warranty claim?", "Contact support with the order number, product serial number if applicable, problem description, and supporting photos or video."),
    _faq("warranty", "proof_of_purchase", "Do I need proof of purchase for warranty service?", "Yes. Use the Northstar Shop invoice or order record as proof of purchase."),
    _faq("warranty", "accidental_damage", "Does the standard warranty cover accidental damage?", "No. The standard warranty covers eligible manufacturing defects, not drops, liquid damage, misuse, or normal wear."),
    _faq("warranty", "warranty_shipping", "Who pays shipping for a warranty claim?", "Northstar Shop provides shipping instructions for approved claims. Do not send a product before receiving authorization."),
    _faq("warranty", "replacement_warranty", "Is a replacement product covered by warranty?", "A replacement is covered for the remainder of the original warranty or 90 days, whichever is longer."),
    _faq("warranty", "manufacturer_warranty", "Should I contact the manufacturer or Northstar Shop?", "Follow the warranty instructions on the product page. Some brands handle claims directly, while others are handled by Northstar Shop."),
    _faq("warranty", "warranty_status", "How can I check my warranty claim status?", "Open Support cases and select the claim, or use the status link in the claim-confirmation email."),
    _faq("warranty", "unauthorized_repair", "Will an unauthorized repair affect my warranty?", "Damage caused by unauthorized repair or modification is not covered and may invalidate the remaining warranty."),
    _faq("warranty", "secondhand_product", "Can a secondhand owner use the warranty?", "Warranty transfer depends on the manufacturer. The original proof of purchase and serial number are required."),

    # Technical support
    _faq("technical_support", "app_not_opening", "The Northstar Shop app will not open.", "Restart the device, install the latest app version, and try again. If it still fails, use the website and report the device and app version to support."),
    _faq("technical_support", "website_not_loading", "Why is the website not loading for me?", "Check your connection, refresh the page, and try a supported browser without extensions. Check the service-status page if the problem continues."),
    _faq("technical_support", "checkout_error", "Checkout displays an error when I submit my order.", "Refresh the cart, confirm required address fields, and retry once. If no order was created, try another supported browser or contact support."),
    _faq("technical_support", "cart_disappeared", "Why did the items in my cart disappear?", "Guest carts use browser storage and can be cleared with cookies or another device. Signed-in carts are retained, but unavailable items may be removed."),
    _faq("technical_support", "page_display", "The page layout looks broken.", "Update the browser, reset page zoom, and temporarily disable content-blocking extensions. Send support a screenshot if the issue remains."),
    _faq("technical_support", "notification_issue", "App notifications are not appearing.", "Enable notifications in both the app settings and device settings, then confirm that battery-saving mode is not restricting the app."),
    _faq("technical_support", "unsupported_browser", "Which web browsers are supported?", "Use a current version of Chrome, Safari, Firefox, or Edge. Older browsers may not support checkout and account-security features."),
    _faq("technical_support", "clear_cache", "Should I clear my browser cache to fix an error?", "Clearing cached files can fix stale pages. Save your cart or sign in first, because clearing site data may remove a guest cart."),
    _faq("technical_support", "upload_failure", "Why can I not upload a photo to my support case?", "Use a JPG, PNG, or PDF under 10 MB. Rename files with simple characters and try one attachment at a time."),
    _faq("technical_support", "service_status", "How can I check whether Northstar Shop is down?", "Open the service-status page for current incidents and maintenance updates. Avoid repeated payment attempts during a checkout incident."),

    # Privacy
    _faq("privacy", "data_collected", "What personal data does Northstar Shop collect?", "The privacy notice explains data collected for accounts, orders, payments, support, security, and consented communications."),
    _faq("privacy", "delete_data", "How can I ask for my personal data to be deleted?", "Open Settings, select Privacy, and submit a deletion request. Required transaction records may be retained for legal obligations."),
    _faq("privacy", "correct_data", "How do I correct inaccurate personal information?", "Edit available fields in Settings or submit a privacy request for information that cannot be changed in your account."),
    _faq("privacy", "data_export", "Can I request a portable copy of my data?", "Yes. Choose Request data export under Privacy. We will verify the request and email a secure download link when ready."),
    _faq("privacy", "cookie_choices", "Where can I change my cookie preferences?", "Open Cookie settings from the site footer. Essential cookies remain active because the service requires them."),
    _faq("privacy", "marketing_opt_out", "How do I stop promotional emails?", "Use the unsubscribe link in a promotional email or disable marketing under Communication preferences. Order and security emails will continue."),
    _faq("privacy", "data_retention", "How long is my information retained?", "Retention depends on the data and its purpose. The privacy notice describes the applicable periods and legal requirements."),
    _faq("privacy", "privacy_contact", "Who can answer a privacy question?", "Submit the privacy contact form linked in the privacy notice so the specialist team can review your question."),
    _faq("privacy", "minor_data", "Can a child create a Northstar Shop account?", "Accounts are intended for users who meet the minimum age stated in the terms. A parent or guardian should contact support about accidental registration."),
    _faq("privacy", "third_party_sharing", "Does Northstar Shop share data with other companies?", "Data is shared with service providers when needed for functions such as payments and delivery, as explained in the privacy notice."),

    # Security
    _faq("security", "phishing_email", "How can I identify a fake Northstar Shop email?", "Be cautious of urgent payment requests, unexpected attachments, and mismatched links. Sign in directly through the official site instead of the message."),
    _faq("security", "report_phishing", "Where should I report a suspicious message?", "Forward the message to the security-reporting address listed in the Help Center, then delete it without opening attachments."),
    _faq("security", "account_compromised", "I think someone accessed my account.", "Reset the password, sign out all devices, enable two-factor authentication, review account details, and contact support immediately."),
    _faq("security", "payment_scam", "Someone asked me to pay outside Northstar Shop.", "Do not send payment. Northstar Shop orders must be paid through official checkout. Report the message or seller details to support."),
    _faq("security", "support_password", "Will support ever ask for my password?", "No. Support will never request your password, complete card number, or two-factor authentication code."),
    _faq("security", "secure_connection", "How do I know the checkout page is secure?", "Use the official Northstar Shop domain and confirm the browser shows an HTTPS connection before entering payment details."),
    _faq("security", "public_computer", "Is it safe to shop on a shared computer?", "Avoid saving payment details, sign out when finished, and do not select Remember me. A trusted personal device is safer."),
    _faq("security", "breach_notification", "How will customers be told about a data breach?", "If notification is required, Northstar Shop will use verified contact channels and provide guidance through official notices."),
    _faq("security", "suspicious_refund_call", "A caller wants my verification code to issue a refund.", "Do not share the code. Northstar Shop does not require a sign-in or two-factor code to issue a refund."),
    _faq("security", "security_bug", "How can I report a security vulnerability?", "Use the security-reporting instructions in the Help Center and avoid accessing, changing, or exposing other customers' data."),

    # Loyalty rewards
    _faq("loyalty", "join_rewards", "How do I join the rewards program?", "Create or sign in to an account, open Rewards, and accept the program terms. Membership is free."),
    _faq("loyalty", "earn_points", "How are reward points earned?", "Eligible purchases earn points at the rate shown in Rewards. Taxes, delivery fees, gift cards, and excluded products do not earn points."),
    _faq("loyalty", "points_pending", "Why are my reward points pending?", "Points remain pending until the order ships and the return period passes, then move to the available balance."),
    _faq("loyalty", "redeem_points", "How can I use reward points?", "At checkout, choose an available reward amount before payment. Points cannot reduce the order below the minimum displayed."),
    _faq("loyalty", "points_expiry", "Do reward points expire?", "Available points expire after 12 months without an eligible earning or redemption activity. The Rewards page shows upcoming expirations."),
    _faq("loyalty", "returned_order_points", "What happens to points when I return an order?", "Points earned from returned items are removed, and redeemed points attributable to an approved return are restored."),
    _faq("loyalty", "missing_points", "My purchase did not earn reward points.", "Confirm the purchase was eligible and made while signed in. Contact support after the return period if qualifying points are still missing."),
    _faq("loyalty", "transfer_points", "Can I transfer points to another account?", "Reward points cannot be transferred, sold, or combined between customer accounts."),
    _faq("loyalty", "points_cash", "Can reward points be exchanged for cash?", "No. Points have no cash value and can only be redeemed through eligible Northstar Shop transactions."),
    _faq("loyalty", "rewards_tier", "Does the rewards program have membership tiers?", "The pilot rewards program has one membership level; tiered status benefits are not currently offered."),

    # Gift cards
    _faq("gift_cards", "buy_gift_card", "Where can I buy a Northstar Shop gift card?", "Digital gift cards are sold on the Gift cards page and are delivered to the recipient email after payment review."),
    _faq("gift_cards", "gift_card_delivery", "When will an emailed gift card arrive?", "Most digital gift cards arrive within one hour, although payment review can take up to one business day."),
    _faq("gift_cards", "gift_card_balance", "How do I check a gift card balance?", "Open the gift-card balance page and enter the card number and security code."),
    _faq("gift_cards", "redeem_gift_card", "How do I use a gift card online?", "Enter the gift card number and security code in the Gift card field during checkout."),
    _faq("gift_cards", "gift_card_expiry", "Do Northstar Shop gift cards expire?", "Northstar Shop gift cards do not expire, unless local law requires different treatment disclosed at purchase."),
    _faq("gift_cards", "lost_gift_card", "Can a lost gift card be replaced?", "Contact support with the purchase receipt and card details. Replacement is possible only if the unused balance can be verified."),
    _faq("gift_cards", "gift_card_refundable", "Can I return a gift card for a refund?", "Gift cards are non-refundable except where required by law. Purchases made with one follow the normal product return policy."),
    _faq("gift_cards", "multiple_gift_cards", "Can I use more than one gift card on an order?", "Up to three Northstar Shop gift cards can be applied to one online order."),
    _faq("gift_cards", "gift_card_not_working", "Why is my gift card being rejected?", "Check the number, security code, activation status, and balance. Contact support if a valid card is still rejected."),
    _faq("gift_cards", "international_gift_card", "Can I use a gift card in another currency?", "Gift cards can be redeemed only on the regional store and in the currency in which they were issued."),

    # Promotions
    _faq("promotions", "apply_code", "Where do I enter a promotional code?", "Enter the code in the Promotion field at checkout and select Apply before submitting payment."),
    _faq("promotions", "code_invalid", "Why is my promotional code invalid?", "Check its spelling, dates, eligible products, regional restrictions, minimum spend, and whether it has already been used."),
    _faq("promotions", "combine_codes", "Can I combine two promotional codes?", "Only one promotional code can be used per order unless the offer terms explicitly permit stacking."),
    _faq("promotions", "code_after_order", "Can a discount code be added after I place an order?", "Promotional codes cannot be added after checkout. If cancellation is available, you may reorder using a valid code."),
    _faq("promotions", "sale_price", "How long will a sale price remain available?", "Offers run for the period stated in their terms and may end earlier if eligible stock sells out."),
    _faq("promotions", "minimum_spend", "What counts toward a promotion's minimum spend?", "Eligible merchandise after other discounts counts toward the minimum; taxes, shipping, gift cards, and excluded items do not."),
    _faq("promotions", "new_customer_offer", "Who qualifies for the new-customer discount?", "The offer is limited to a customer's first eligible order and is subject to the account, product, and date restrictions in its terms."),
    _faq("promotions", "promotion_return", "What happens to my discount if I return part of an order?", "The refund is based on the discounted amount paid. If remaining items no longer meet an offer condition, the refund may be adjusted."),
    _faq("promotions", "price_match", "Does Northstar Shop match competitors' prices?", "Northstar Shop does not currently offer competitor price matching."),
    _faq("promotions", "student_discount", "Is there a student discount?", "A student discount is available only when advertised through the verification partner and subject to the current offer terms."),

    # Customer support
    _faq("customer_support", "contact_support", "How can I contact customer support?", "Use chat or the contact form in the Help Center. Available channels and current operating hours are displayed there."),
    _faq("customer_support", "support_hours", "When is customer support open?", "Current support hours are listed in the Help Center and may vary by channel, region, and public holiday."),
    _faq("customer_support", "case_status", "How can I check my support case?", "Open Support cases in your account or use the secure link in the case-confirmation email."),
    _faq("customer_support", "case_reply", "How do I add information to an existing support case?", "Reply through the case page or to the case email without changing its reference number."),
    _faq("customer_support", "duplicate_case", "Should I open another case if support has not replied?", "No. Add information to the existing case; duplicate cases can delay review and separate important details."),
    _faq("customer_support", "escalate_case", "Can I ask for my case to be escalated?", "Yes. Reply to the open case with the reason escalation is needed. A specialist will review eligible requests."),
    _faq("customer_support", "supported_languages", "Which languages does customer support offer?", "Available languages are shown when you choose a support channel. Coverage and hours vary by language."),
    _faq("customer_support", "send_attachment", "Can I attach evidence to a support request?", "Yes. The case form accepts JPG, PNG, and PDF files under 10 MB. Remove unrelated personal information first."),
    _faq("customer_support", "complaint", "How do I make a formal complaint?", "Select Complaint on the contact form, describe the issue and desired resolution, and include related order or case numbers."),
    _faq("customer_support", "support_identity_check", "Why is support asking me to verify my identity?", "Verification protects account and order information. Support will use approved checks but will never ask for your password or security code."),
]


def build_records() -> list[dict[str, str]]:
    """Return numbered records after enforcing pilot invariants."""
    if len(FAQ_RECORDS) != 200:
        raise ValueError(f"Expected 200 seed records, found {len(FAQ_RECORDS)}")

    records: list[dict[str, str]] = []
    for position, record in enumerate(FAQ_RECORDS, start=1):
        records.append({"document_id": f"FAQ-{position:04d}", **record, "data_origin": "synthetic"})
    return records


def write_dataset(output_path: Path, *, overwrite: bool = False) -> None:
    """Write the deterministic CSV while protecting an existing raw file."""
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Refusing to replace existing raw dataset: {output_path}. Use --force to regenerate it."
        )
    records = build_records()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true", help="Replace an existing generated CSV.")
    args = parser.parse_args()
    write_dataset(args.output, overwrite=args.force)
    print(f"Wrote {len(FAQ_RECORDS)} synthetic FAQ records to {args.output}")


if __name__ == "__main__":
    main()
