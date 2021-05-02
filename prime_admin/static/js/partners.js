$(document).ready(function(){

    var dtbl_current_branches = $("#tbl_branches_inline").DataTable({
        "dom": 'rtip',
        "bSort": false,
        "bInfo": false,
        "bPaginate": false,
    });

    var dtbl_add_branches = $("#tbl_add_branches_inline").DataTable({
        "dom": 'rtip',
        "bSort": false,
        "bInfo": false,
        "bPaginate": false,
    });

    $("#tbl_branches_inline").on('click', '.btn-remove', function(){


        var $row = $(this).closest('tr');

        var data = dtbl_current_branches.row($row).data();
        
        var output = data[0].replace(`name="branches[]"`, '');

        var newRow = dtbl_add_branches.row.add([
            output,
            data[1],
            '',
            '',
            '',
            `<button type="button" class="mb-2 mr-2 btn-transition btn btn-outline-success btn-add">Add</button>`
        ]);

        dtbl_add_branches.row(newRow).column(0).nodes().to$().addClass('myHiddenColumn');
        dtbl_add_branches.row(newRow).draw();
        dtbl_current_branches.row($row).remove().draw();
    });

    $("#tbl_add_branches_inline").on('click', '.btn-add',function(){

        var $row = $(this).closest('tr');

        var data = dtbl_add_branches.row($row).data();

        var stringAppended = ` name="branches[]"`;
        var output = [data[0].slice(0, 6), stringAppended, data[0].slice(6)].join('');

        var newRow = dtbl_current_branches.row.add([
            output,
            data[1],
            '',
            '',
            '',
            `<button type="button" class="mb-2 mr-2 btn-transition btn btn-outline-danger btn-remove">Remove</button>`
        ]);

        dtbl_current_branches.row(newRow).column(0).nodes().to$().addClass('myHiddenColumn');
        dtbl_current_branches.row(newRow).draw();
        dtbl_add_branches.row($row).remove().draw();
    });
});