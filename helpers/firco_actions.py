def process_firco_transaction(fircoPage, transaction, action, user_comment):
    fircoPage.go_to_transaction_details(transaction, user_comment)
    if action == "STP-RELEASE":
        fircoPage.perform_action(action)
    else:
        fircoPage.escalateBtn.click()
    fircoPage.logout()
