# TEST LABELS for chapter 4. Remove this file before shipping.
# Route tests play the whole chapter from preset meters; system tests jump
# straight into the office with preset principles.

label ch4_test_architect:
    $ clarity = 12
    $ integrity = 12
    $ bond = 6
    $ watch = 4
    $ told_mira = True
    $ kept_journal = True
    $ p_truth = 6
    jump chapter4

label ch4_test_chosen:
    $ bond = 14
    $ watch = 3
    $ clarity = 4
    $ integrity = 6
    $ p_share = -6
    jump chapter4

label ch4_test_lantern:
    $ watch = 12
    $ bond = 5
    $ clarity = 5
    $ integrity = 5
    $ p_govern = -6
    jump chapter4

label ch4_test_longfog:
    $ risky = 10
    $ fog = 9
    $ integrity = 2
    $ bond = 4
    $ p_rest = 6
    jump chapter4

label ch4_test_snapshot:
    $ bond = 2
    $ watch = 2
    $ p_exit = -6
    jump chapter4

label ch4_test_sys_less_plus:
    $ p_less = 5
    $ p_truth = 1
    $ p_share = -1
    $ p_rest = 0
    $ p_spirits = 1
    $ p_govern = -1
    $ p_exit = 0
    $ ch4_route = "snapshot"
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_less_minus:
    $ p_less = -5
    $ p_truth = 1
    $ p_share = -1
    $ p_rest = 0
    $ p_spirits = 1
    $ p_govern = -1
    $ p_exit = 0
    $ ch4_route = "architect"
    $ ch4_ashveil_fasts = True
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_truth_plus:
    $ p_truth = 5
    $ p_share = -1
    $ p_rest = 0
    $ p_spirits = 1
    $ p_govern = -1
    $ p_exit = 0
    $ p_less = 1
    $ ch4_route = "architect"
    $ ch4_ashveil_fasts = True
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_truth_minus:
    $ p_truth = -5
    $ p_share = -1
    $ p_rest = 0
    $ p_spirits = 1
    $ p_govern = -1
    $ p_exit = 0
    $ p_less = 1
    $ ch4_route = "chosen"
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_share_plus:
    $ p_share = 5
    $ p_truth = 1
    $ p_rest = 0
    $ p_spirits = 1
    $ p_govern = -1
    $ p_exit = 0
    $ p_less = 1
    $ ch4_route = "longfog"
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_share_minus:
    $ p_share = -5
    $ p_truth = 1
    $ p_rest = 0
    $ p_spirits = 1
    $ p_govern = -1
    $ p_exit = 0
    $ p_less = 1
    $ ch4_route = "lantern"
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_rest_plus:
    $ p_rest = 5
    $ p_truth = 1
    $ p_share = -1
    $ p_spirits = 1
    $ p_govern = -1
    $ p_exit = 0
    $ p_less = 1
    $ ch4_route = "longfog"
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_rest_minus:
    $ p_rest = -5
    $ p_truth = 1
    $ p_share = -1
    $ p_spirits = 1
    $ p_govern = -1
    $ p_exit = 0
    $ p_less = 1
    $ ch4_route = "snapshot"
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_spirits_plus:
    $ p_spirits = 5
    $ p_truth = 1
    $ p_share = -1
    $ p_rest = 0
    $ p_govern = -1
    $ p_exit = 0
    $ p_less = 1
    $ ch4_route = "lantern"
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_spirits_minus:
    $ p_spirits = -5
    $ p_truth = 1
    $ p_share = -1
    $ p_rest = 0
    $ p_govern = -1
    $ p_exit = 0
    $ p_less = 1
    $ ch4_route = "chosen"
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_govern_plus:
    $ p_govern = 5
    $ p_truth = 1
    $ p_share = -1
    $ p_rest = 0
    $ p_spirits = 1
    $ p_exit = 0
    $ p_less = 1
    $ ch4_route = "architect"
    $ ch4_ashveil_fasts = True
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_govern_minus:
    $ p_govern = -5
    $ p_truth = 1
    $ p_share = -1
    $ p_rest = 0
    $ p_spirits = 1
    $ p_exit = 0
    $ p_less = 1
    $ ch4_route = "lantern"
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_exit_plus:
    $ p_exit = 5
    $ p_truth = 1
    $ p_share = -1
    $ p_rest = 0
    $ p_spirits = 1
    $ p_govern = -1
    $ p_less = 1
    $ ch4_route = "chosen"
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_exit_minus:
    $ p_exit = -5
    $ p_truth = 1
    $ p_share = -1
    $ p_rest = 0
    $ p_spirits = 1
    $ p_govern = -1
    $ p_less = 1
    $ ch4_route = "snapshot"
    $ bond = 7
    $ watch = 7
    jump ch4_rehearsal

label ch4_test_sys_open:
    $ ch4_route = "snapshot"
    jump ch4_rehearsal

label ch4_test_cousin:
    $ p_exit = 3
    $ p_govern = 3
    $ ch4_route = "chosen"
    $ bond = 12
    jump ch4_rehearsal
