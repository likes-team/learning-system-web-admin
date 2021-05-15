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
            $("#amount").prop('readonly', true);

            balance = 7000 - $("#amount").val();
        }
        else if (this.value == 'installment') {
            $("#amount").val(0);
            $("#amount").prop('readonly', false);

            balance = 7800 - $("#amount").val();
        }

        $("#balance").val(balance);
    });

    var dtbl_search = $("#tbl_mdl_clients").DataTable({
        pageLength: 10,
        columnDefs: [
            {
                "targets": 0,
                "visible": false,
            },
        ],
        ajax: {
            url: "/learning-management/api/dtbl/mdl-pre-registered-clients-registration",
        }
    });


    $('#tbl_mdl_clients tbody').on( 'click', 'tr', function () {
        if ( $(this).hasClass('selected') ) {
            $(this).removeClass('selected');
        }
        else {
            dtbl_search.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
        }
    } );

    $('#btn_confirm').click( function () {
        var selected = dtbl_search.row('.selected').data();
        
        $.ajax({
            url: '/learning-management/api/clients/' + selected[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                if(response.data.status == "pre_registered"){
                    console.log(response.data);

                    $("#client_id").val(response.data.id);
                    $("#lname").val(response.data.lname);
                    $("#fname").val(response.data.fname);
                    $("#mname").val(response.data.mname);
                    $("#suffix").val(response.data.suffix);
                    $("#contact_number").val(response.data.contact_number);
                    $("#email").val(response.data.email);
                    $("#address").val(response.data.address);

                    var formattedDate = new Date(response.data.birth_date);
                    var d = ('0' + formattedDate.getDate()).slice(-2);
                    var m =  ('0' + (formattedDate.getMonth()+1)).slice(-2);
                    var y = formattedDate.getFullYear();

                    $("#birth_date").val(y + "-" + m + "-" + d);
            
                    $("#lname").prop('readonly', true);
                    $("#fname").prop('readonly', true);
                    $("#mname").prop('readonly', true);
                    $("#suffix").prop('readonly', true);
                    $("#contact_number").prop('readonly', true);
                    $("#birth_date").prop('readonly', true);
                    $("#address").prop('readonly', true);
                    $("#email").prop('readonly', true);

                } else if(response.data.status == "oriented"){
                    $("#client_id").val(response.data.id);
                    $("#lname").val(response.data.lname);
                    $("#fname").val(response.data.fname);
                    $("#contact_number").val(response.data.contact_number);
                    $("#contact_person").val(response.data.contact_person);

                    $("#lname").prop('readonly', true);
                    $("#fname").prop('readonly', true);
                    $("#contact_number").prop('readonly', true);
                    $("#contact_person").prop('disabled', true);
                }
            }
        });
    });

    $('#btn_clear_entries').click( function () {
        $("#client_id").val('');
        $("#lname").val('');
        $("#fname").val('');
        $("#mname").val('');
        $("#suffix").val('');
        $("#contact_number").val('');
        $("#birth_date").val('');
        $("#email").val('');
        $("#address").val('');
        $("#contact_person").val('');

        $("#lname").prop('readonly', false);
        $("#fname").prop('readonly', false);
        $("#mname").prop('readonly', false);
        $("#suffix").prop('readonly', false);
        $("#contact_number").prop('readonly', false);
        $("#birth_date").prop('readonly', false);
        $("#email").prop('readonly', false);
        $("#address").prop('readonly', false);
        $("#contact_person").prop('disabled', false);
    });
});
