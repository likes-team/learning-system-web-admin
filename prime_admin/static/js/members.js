$(document).ready(function(){
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
            }
        }
    });

    // Command: toastr["success"](" ", "Saved Successfully!")

    toastr.options = {
    "closeButton": true,
    "debug": false,
    "newestOnTop": false,
    "progressBar": false,
    "positionClass": "toast-top-center",
    "preventDuplicates": false,
    "onclick": null,
    "showDuration": "3000",
    "hideDuration": "1000",
    "timeOut": "5000",
    "extendedTimeOut": "1000",
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
    }

    var table = $('#tbl_members').DataTable({
        "dom": 'rtip',
        "pageLength": 20,
        "order": [[ 1, 'asc' ]],
        "processing": true,
        "serverSide": true,
        "autoWidth": false,
        "columnDefs": [
            { "visible": false, "targets": 0},
            { "width": 100, "targets": 15},
            { "width": "10px", "targets": 12}
        ],
        "ajax": {
            "url": "/learning-management/dtbl/members",
            "data": function (d) {
                d.branch = $("#branch").val();
                d.batch_no = $("#batch_no").val();
                d.schedule = $("#schedule").val();
            },
            "dataSrc": function(json){
                $("#total_installment").html("₱" + json.totalInstallment + ".00");
                $("#total_full_payment").html("₱" + json.totalFullPayment + ".00");
                $("#total_premium_payment").html("₱" + json.totalPremiumPayment + ".00");
                $("#total_payment").html("₱" + json.totalPayment + ".00");
                $("#sales_today").html("₱" + json.salesToday + ".00");

                return json.data;
            }
        }
    });

    // $('#tbl_members tbody').on('click', 'tr', function () {
    //     var data = table.row( this ).data();
        
    //     $("#viewModal").modal('toogle');
    //     $("#viewModal").modal('show');
    // } );

    
    $('#tbl_members tbody').on('click', '.btn-edit', function () {
        var data = table.row( $(this).parents('tr')).data();
        
        $.ajax({
            url: '/learning-management/api/members/' + data[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                $("#edit_client_id").val(response.data.id);
                $("#edit_last_name").val(response.data.lname);
                $("#edit_first_name").val(response.data.fname);
                $("#edit_middle_name").val(response.data.mname);
                $("#edit_suffix").val(response.data.suffix);
                $("#edit_mode_of_payment").val(response.data.mode_of_payment.toUpperCase());
                $("#edit_amount").val(response.data.amount);
                $("#edit_balance").val(response.data.balance);

                $("#tbl_edit_payment_history > tbody").empty();

                for(i=0; i < response.data.payments.length; i++){
                    $('#tbl_edit_payment_history > tbody:first').append(
                        `<tr>
                        <td>${response.data.payments[i].amount}</td>
                        <td>${response.data.payments[i].current_balance}</td>
                        <td>${response.data.payments[i].date}</td>
                        </tr>`
                        );
                }

                console.log(response.data);
                $('#book_none').prop('checked', false);
                $('#book1').prop('checked', false);
                $('#book2').prop('checked', false);

                if(response.data.books.book_none){
                    $('#book_none').prop('checked', true);
                } else if(response.data.books.volume1){
                    $('#book1').prop('checked', true);
                } else if(response.data.books.volume2){
                    $('#book2').prop('checked', true);
                }

                if(response.data.uniforms.uniform_none){
                   $("#uniform_none").prop("checked", true);
                } else if(response.data.uniforms.uniform_xs){
                    $("#uniform_xs").prop("checked", true);
                } else if(response.data.uniforms.uniform_s){
                    $("#uniform_s").prop("checked", true);
                } else if(response.data.uniforms.uniform_m){
                    $("#uniform_m").prop("checked", true);
                } else if(response.data.uniforms.uniform_l){
                    $("#uniform_l").prop("checked", true);
                } else if(response.data.uniforms.uniform_xl){
                    $("#uniform_xl").prop("checked", true);
                } else if(response.data.uniforms.uniform_xxl){
                    $("#uniform_xxl").prop("checked", true);
                }
            }
        });
    } );
        
    $('#tbl_members tbody').on('click', '.btn-view', function () {
        var data = table.row( $(this).parents('tr') ).data();
        
        $.ajax({
            url: '/learning-management/api/members/' + data[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                $("#client_id").val(response.data.id);
                $("#view_last_name").val(response.data.lname);
                $("#view_first_name").val(response.data.fname);
                $("#view_middle_name").val(response.data.mname);
                $("#view_suffix").val(response.data.suffix);
                $("#view_batch_no").val(response.data.batch_no);
                $("#view_schedule").val(response.data.schedule);
                $("#view_branch").val(response.data.branch);
                $("#view_contact_person").val(response.data.contact_person);
                $("#view_date_of_birth").val(response.data.birth_date);
                $("#view_passport").val(response.data.passport);
                $("#view_contact_no").val(response.data.contact_no);
                $("#view_email").val(response.data.email);
                $("#view_address").val(response.data.address);
                $("#view_mode_of_payment").val(response.data.mode_of_payment.toUpperCase());
                $("#view_book").val(response.data.book);
                $("#view_uniform").val(response.data.uniform);
                $("#view_amount").val(response.data.amount);
                $("#view_balance").val(response.data.balance);

                $("#tbl_payment_history > tbody").empty();

                for(i=0; i < response.data.payments.length; i++){
                    $('#tbl_payment_history > tbody:first').append(
                        `<tr>
                        <td>${response.data.payments[i].amount}</td>
                        <td>${response.data.payments[i].current_balance}</td>
                        <td>${response.data.payments[i].date}</td>
                        </tr>`
                        );
                }
            }
        });

    } );

    $("#btn_edit").click(function(){
        if($(this).html() == "Edit"){
            $(this).html("Save");
            $("#view_last_name").prop('disabled', false);
            $("#view_first_name").prop('disabled', false);
            $("#view_middle_name").prop('disabled', false);
            $("#view_suffix").prop('disabled', false);
            // $("#view_schedule").prop('disabled', false);
            // $("#view_date_of_birth").prop('disabled', false);
            $("#view_passport").prop('disabled', false);
            $("#view_contact_no").prop('disabled', false);
            $("#view_email").prop('disabled', false);
            $("#view_address").prop('disabled', false);
        }else if ($(this).html() == "Save"){
            $(this).html("Edit");
            $("#view_last_name").prop('disabled', true);
            $("#view_first_name").prop('disabled', true);
            $("#view_middle_name").prop('disabled', true);
            $("#view_suffix").prop('disabled', true);
            // $("#view_schedule").prop('disabled', true);
            // $("#view_date_of_birth").prop('disabled', true);
            $("#view_passport").prop('disabled', true);
            $("#view_contact_no").prop('disabled', true);
            $("#view_email").prop('disabled', true);
            $("#view_address").prop('disabled', true);

            var lname = $("#view_last_name").val();
            var fname = $("#view_first_name").val();
            var mname = $("#view_middle_name").val();
            var suffix = $("#view_suffix").val();
            var birth_date = $("#view_date_of_birth").val();
            var passport = $("#view_passport").val();
            var contact_no = $("#view_contact_no").val();
            var email = $("#view_email").val();
            var address = $("#view_address").val();

            $.ajax({
                url: "/learning-management/api/members/" + $("#client_id").val() + "/edit",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    "lname": lname,
                    "fname": fname,
                    "mname": mname,
                    "suffix": suffix,
                    "birth_date": birth_date,
                    "passport": passport,
                    "contact_no": contact_no,
                    "email": email,
                    "address": address
                }),
                contentType: "application/json; charset=utf-8",
                success: function(response){
                    if(response.result){
                        table.ajax.reload();
                        toastr.success("Saved Successfully!");
                    }else{
                        toastr.error("Error Occured!, Saving Failed");
                    }
                }
            });
        }
    });


    $("#book1").click(function(){
        $('#book_none').prop('checked', false);
    });

    $("#book2").click(function(){
        $('#book_none').prop('checked', false);
    });

    $("#book_none").click(function(){
        $('#book1').prop('checked', false);
        $('#book2').prop('checked', false);
    });

    $("#btn_print").click(function(){
        var branch = $("#branch").val();
        var batch_no = $("#batch_no").val();
        var schedule = $("#schedule").val();
        location.href = PDF_URL + `?branch=${branch}&batch_no=${batch_no}&schedule=${schedule}`;
    });


    $("#branch").change(function(){
        BRANCH = $(this).val();
        table.ajax.reload();
    });

    $("#batch_no").change(function(){
        BATCH_NO = $(this).val();
        table.ajax.reload();
    });

    $("#schedule").change(function(){
        SCHEDULE = $(this).val();
        table.ajax.reload();
    });
});
