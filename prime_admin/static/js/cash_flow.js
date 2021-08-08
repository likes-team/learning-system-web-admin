function updateDataTableSelectAllCtrl(table) {
    var $table = table.table().node();
    var $chkbox_all = $('tbody input[type="checkbox"]', $table);
    var $chkbox_checked = $('tbody input[type="checkbox"]:checked', $table);
    var chkbox_select_all = $('thead input[type="checkbox"]', $table).get(0);

    // If none of the checkboxes are checked
    if ($chkbox_checked.length === 0) {
        chkbox_select_all.checked = false;
        if ('indeterminate' in chkbox_select_all) {
            chkbox_select_all.indeterminate = false;
        }

        // If all of the checkboxes are checked
    } else if ($chkbox_checked.length === $chkbox_all.length) {
        chkbox_select_all.checked = true;
        if ('indeterminate' in chkbox_select_all) {
            chkbox_select_all.indeterminate = false;
        }

        // If some of the checkboxes are checked
    } else {
        chkbox_select_all.checked = true;
        if ('indeterminate' in chkbox_select_all) {
            chkbox_select_all.indeterminate = true;
        }
    }
}

$(document).ready(function () {
    var subscribers_selected = [];

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
            }
        }
    });

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

    var dtbl_statement = $('#tbl_statement').DataTable({
        "dom": 'rtip',
        "pageLength": 100,
        "order": [[1, 'asc']],
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "columnDefs": [
            { "visible": false, "targets": 8 }
        ],
        "ajax": {
            "url": "/learning-management/dtbl/get-cash-flow",
            "data": function (d) {
                d.branch = $("#btn_branch_label").val();
                d.from_what = "sales"
            },
            "dataSrc": function (json) {
                var remaining = parseFloat(json.remaining).toFixed(2);
                var net = parseFloat(json.net).toFixed(2);
                var fund1 = parseFloat(json.fund1).toFixed(2);
                var fund2 = parseFloat(json.fund2).toFixed(2);

                $("#total_gross_sales").html("₱" + json.totalGrossSales);
                $("#remaining").html("₱" + remaining);
                $("#net").html("₱" + net);
                $("#fund1").html("₱" + fund1);
                $("#fund2").html("₱" + fund2);
                $("#final_fund1").html("₱" + json.finalFund1);
                $("#final_fund2").html("₱" + json.finalFund2);
                return json.data;
            }
        }
    });

    var dtbl_fund_statement = $('#tbl_fund_statement').DataTable({
        "dom": 'rtip',
        "pageLength": 100,
        "order": [[1, 'asc']],
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "columnDefs": [
            { "visible": false, "targets": 8 }
        ],
        "ajax": {
            "url": "/learning-management/dtbl/get-cash-flow",
            "data": function (d) {
                d.branch = $("#btn_branch_label").val();
                d.from_what = "fund"
            },
            "dataSrc": function (json) {
                var remaining = parseFloat(json.remaining).toFixed(2);
                var net = parseFloat(json.net).toFixed(2);
                var fund1 = parseFloat(json.fund1).toFixed(2);
                var fund2 = parseFloat(json.fund2).toFixed(2);

                $("#total_gross_sales").html("₱" + json.totalGrossSales);
                $("#remaining").html("₱" + remaining);
                $("#net").html("₱" + net);
                $("#fund1").html("₱" + fund1);
                $("#fund2").html("₱" + fund2);
                $("#final_fund1").html("₱" + json.finalFund1);
                $("#final_fund2").html("₱" + json.finalFund2);
                return json.data;
            }
        }
    });

    $("#div_branch_buttons").on('click', '.btn-branch', function () {
        var branch_name = $(this).html();

        // if(!(localStorage.getItem('sessSubArea') == _sub_area_name)){
        $("#btn_branch_label").html(branch_name.toUpperCase());
        $("#btn_branch_label").val($(this).val());
        $("#card_header_label").html(branch_name);

        $('#btn_branch_label').trigger('change');
        // dtbl_subscribers.ajax.url(`/bds/api/sub-areas/${$(this).val()}/subscribers`).load();
        // }

    });

    $("#btn_branch_label").change(function () {
        dtbl_statement.ajax.reload();
        dtbl_fund_statement.ajax.reload();
    });

    var groupColumn = 1;

    var dtbl_pre_deposit = $("#tbl_mdl_pre_deposit").DataTable({
        ajax: {
            url: "/learning-management/api/dtbl/mdl-pre-deposit",
        },
        pageLength: 100,
        ordering: false,
        "order": [[ groupColumn, 'asc' ]],
        columnDefs: [
            {
                'targets': 1,
                'visible': false
            },
            {
                'targets': 0,
                'searchable': false,
                'orderable': false,
                'width': '1%',
                'className': 'dt-body-center',
                'checkboxes': {
                    'selectRow': true
                }
            },
        ],
        select: {
            'style': 'multi'
        },
        order: [[1, 'asc']],
        'rowCallback': function (row, data, dataIndex) {
            // Get row ID
            var rowId = data[0];

            // If row ID is in the list of selected row IDs
            if ($.inArray(rowId, subscribers_selected) !== -1) {
                $(row).find('input[type="checkbox"]').prop('checked', true);
                $(row).addClass('selected');
            }
        },
        "drawCallback": function ( settings ) {
            var api = this.api();
            var rows = api.rows( {page:'current'} ).nodes();
            var last=null;
 
            api.column(groupColumn, {page:'current'} ).data().each( function ( group, i ) {
                if ( last !== group ) {
                    $(rows).eq( i ).before(
                        '<tr style="background-color: lightcyan !important"><td colspan="7">REGISTRATION NO.: '+group+'</td></tr>'
                    );
 
                    last = group;
                }
            } );
        }
    });

    // Handle click on checkbox
    $('#tbl_mdl_pre_deposit tbody').on('click', 'input[type="checkbox"]', function (e) {
        var $row = $(this).closest('tr');

        // Get row data
        var data = dtbl_pre_deposit.row($row).data();

        // Get row ID
        var rowId = data[0];

        // Determine whether row ID is in the list of selected row IDs
        var index = $.inArray(rowId, subscribers_selected);

        // If checkbox is checked and row ID is not in list of selected row IDs
        if (this.checked && index === -1) {
            subscribers_selected.push(rowId);

            // Otherwise, if checkbox is not checked and row ID is in list of selected row IDs
        } else if (!this.checked && index !== -1) {
            subscribers_selected.splice(index, 1);
        }

        if (this.checked) {
            var last_total_val = parseFloat($("#pre_deposit_amount").val());
            var new_total_val = last_total_val + parseFloat(data[6]);
            $("#pre_deposit_amount").val(new_total_val);

            $row.addClass('selected');
        } else {
            var last_total_val = parseFloat($("#pre_deposit_amount").val()); 
            var new_total_val = last_total_val - parseFloat(data[6]);
            $("#pre_deposit_amount").val(new_total_val);
            $row.removeClass('selected');
        }

        // Update state of "Select all" control
        updateDataTableSelectAllCtrl(dtbl_pre_deposit);

        // Prevent click event from propagating to parent
        e.stopPropagation();
    });


    // Handle click on table cells with checkboxes
    $('#tbl_mdl_pre_deposit').on('click', 'tbody td, thead th:first-child', function (e) {
        $(this).parent().find('input[type="checkbox"]').trigger('click');
    });


    // Handle click on "Select all" control
    $('thead input[type="checkbox"]', dtbl_pre_deposit.table().container()).on('click', function (e) {
        if (this.checked) {
            $('#tbl_mdl_pre_deposit tbody input[type="checkbox"]:not(:checked)').trigger('click');
        } else {
            $('#tbl_mdl_pre_deposit tbody input[type="checkbox"]:checked').trigger('click');
        }

        // Prevent click event from propagating to parent
        e.stopPropagation();
    });


    // Handle table draw event
    dtbl_pre_deposit.on('draw', function () {
        // Update state of "Select all" control
        updateDataTableSelectAllCtrl(dtbl_pre_deposit);
    });

    $("#btn_confirm_pre_deposit").click(function () {
        var to_pre_deposit_list = [];

        dtbl_pre_deposit.rows('.selected').data().each(function(value, index){
            to_pre_deposit_list.push(
                {
                    'payment_id': value[0],
                    'full_registration_number': value[1],
                }
            )
        });

        $.ajax({
            url: "/learning-management/api/to-pre-deposit",
            type: "POST",
            dataType: "json",
            data: JSON.stringify({
                'payments_selected': to_pre_deposit_list}),
            contentType: "application/json; charset=utf-8",
            success: function(response){
                if(response.result){
                    dtbl_pre_deposit.ajax.reload();
                    toastr.success("Saved Successfully!");
                }else{
                    toastr.error("Error Occured!, Saving Failed");
                }
            }
        });
    });

    var dtbl_deposit = $("#tbl_mdl_deposit").DataTable({
        ajax: {
            url: "/learning-management/api/dtbl/mdl-deposit",
            "dataSrc": function(json){
                if($("#from_what").val() == "Sales"){
                    $("#amount").val(json.deposit_amount);
                }
    
                return json.data;
            }
        },
        pageLength: 100,
        ordering: false,
        "order": [[ 0, 'asc' ]],
        columnDefs: [
            {
                'targets': 0,
                'visible': false,
                'searchable': false,
                'orderable': false,
                'width': '1%',
                'className': 'dt-body-center',
            },
        ],
        select: {
            'style': 'multi'
        },
        order: [[1, 'asc']],
        "drawCallback": function ( settings ) {
            var api = this.api();
            var rows = api.rows( {page:'current'} ).nodes();
            var last=null;
 
            api.column(0, {page:'current'} ).data().each( function ( group, i ) {
                if ( last !== group ) {
                    $(rows).eq( i ).before(
                        '<tr style="background-color: lightcyan !important"><td colspan="6">REGISTRATION NO.: '+group+'</td></tr>'
                    );
 
                    last = group;
                }
            } );
        },

    });


    $("#from_what").change(function(){
        if($(this).val() == "Sales"){
            dtbl_deposit.ajax.reload();
            $("#amount").prop('readonly', true);
            $("#tbl_deposit").show();
        } else{
            $("#amount").val(0);
            $("#amount").prop('readonly', false);
            $("#tbl_deposit").hide();
        }
    })
});