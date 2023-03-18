$(document).ready(function(){
    var start = moment().startOf('month');
    var end = moment().endOf('month');

    function cb(start, end) {
        $('#filter_date span').html(start.format('MMMM D, YYYY') + ' - ' + end.format('MMMM D, YYYY'));
    }

    $('#filter_date').daterangepicker({
        startDate: start,
        endDate: end,
        ranges: {
            'January': [moment().month(0).startOf('month'), moment().month(0).endOf('month')],
           'February': [moment().month(1).startOf('month'), moment().month(1).endOf('month')],
           'March': [moment().month(2).startOf('month'), moment().month(2).endOf('month')],
           'April': [moment().month(3).startOf('month'), moment().month(3).endOf('month')],
           'May': [moment().month(4).startOf('month'), moment().month(4).endOf('month')],
           'June': [moment().month(5).startOf('month'), moment().month(5).endOf('month')],
           'July': [moment().month(6).startOf('month'), moment().month(6).endOf('month')],
           'August': [moment().month(7).startOf('month'), moment().month(7).endOf('month')],
           'September': [moment().month(8).startOf('month'), moment().month(8).endOf('month')],
           'October': [moment().month(9).startOf('month'), moment().month(9).endOf('month')],
           'November': [moment().month(10).startOf('month'), moment().month(10).endOf('month')],
           'December': [moment().month(11).startOf('month'), moment().month(11).endOf('month')],
           'This Month': [moment().startOf('month'), moment().endOf('month')],
           'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        }
    }, cb);
    cb(start, end);

});