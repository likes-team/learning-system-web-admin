$(document).ready(function(){

    $("#amount").change(function(){
        var payment_mode = $('input[name="payment_modes"]:checked').val();
        var balance;

        if (payment_mode == "full_payment"){
            balance = 7000 - $(this).val();
        } else if (payment_mode == "installment") {
            balance = 7800 - $(this).val();
        }

        $("#balance").val(balance);
    });

    $('input[type=radio][name=payment_modes]').change(function() {
        var balance;

        if (this.value == 'full_payment') {
            balance = 7000 - $("#amount").val();
        }
        else if (this.value == 'installment') {
            balance = 7800 - $("#amount").val();
        }

        $("#balance").val(balance);
    });

});
