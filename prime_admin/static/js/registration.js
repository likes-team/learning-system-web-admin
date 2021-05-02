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

    $('#amount').on('input', function () {
        var payment_mode = $('input[name="payment_modes"]:checked').val();
        
        var value = $(this).val();
        
        if (payment_mode == "full_payment"){
            if ((value !== '') && (value.indexOf('.') === -1)) {
            
                $(this).val(Math.max(Math.min(value, 7000), -7000));
            }
        } else if (payment_mode == "installment") {
            if ((value !== '') && (value.indexOf('.') === -1)) {
            
                $(this).val(Math.max(Math.min(value, 4000), -4000));
            }
        }
    
    });

    $('input[type=radio][name=payment_modes]').change(function() {
        var balance;

        if (this.value == 'full_payment') {
            $("#amount").val(7000);

            balance = 7000 - $("#amount").val();
        }
        else if (this.value == 'installment') {
            $("#amount").val(0);

            balance = 7800 - $("#amount").val();
        }

        $("#balance").val(balance);
    });

});
