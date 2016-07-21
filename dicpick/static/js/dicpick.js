$(function() {
  // Initialize the assignees select box.

  var pathParts = window.location.pathname.split('/');
  var eventPathPrefix = pathParts[1] + '/' + pathParts[2];  // pathParts[0] is expected to be an empty string.
  var tagAutoCompleteUrl = eventPathPrefix + '/tags/autocomplete/';
  var participantAutocompleteUrl = eventPathPrefix + '/participants/autocomplete/';

  $('.with-select2 select.field-assignees').each(function() {
    var numPeople = parseInt($(this).closest('tr').find('input.field-num_people').val());
    $(this).select2({
      ajax: {
        url: participantAutocompleteUrl,
        dataType: 'json',
        delay: 250,
        cache: true,
        data: function(params) {
          return {
            q: params.term,
            d: $(this).attr('dp-for-date'),
            t: $(this).attr('dp-for-tags')
          };
        }
      },
      escapeMarkup: function (markup) { return markup; },  // Allow markup in our template.
      templateResult: function(item) {
        function classForProp(prop) {
          return item[prop] ? ' ' + prop.replace(/_/g, '-') : '';
        }
        return '<div class="assignee-option' +
                            classForProp('disqualified_for_date') +
                            classForProp('disqualified_for_tags') + '"' +
                  (item.tooltip ? ('data-toggle="tooltip" title="' + item.tooltip + '"') : '') +
               '>' + item.text + '</div>';
      },
      minimumInputLength: 2,
      maximumSelectionLength: numPeople
    });
  });

  $('.with-select2 select.field-do_not_assign_to').each(function() {

    $(this).select2({
      ajax: {
        url: participantAutocompleteUrl,
        dataType: 'json',
        delay: 250,
        cache: true,
        data: function (params) {
          return {
            q: params.term
          };
        }
      },
      escapeMarkup: function (markup) {
        return markup;
      },  // Allow markup in our template.
      templateResult: function (item) {
        return '<div class="do-not-assign-to-option">' + item.text + '</div>';
      },
      minimumInputLength: 2
    });
  });

  $('select.field-do_not_assign_with').each(function() {

    $(this).select2({
      ajax: {
        url: participantAutocompleteUrl,
        dataType: 'json',
        delay: 250,
        cache: true,
        data: function(params) {
          return {
            q: params.term
          };
        }
      },
      escapeMarkup: function (markup) { return markup; },  // Allow markup in our template.
      templateResult: function(item) {
        return '<div class="do-not-assign-with-option">' + item.text + '</div>';
      },
      minimumInputLength: 2
    });
  });

  $('select.field-tags').each(function() {

    $(this).select2({
      ajax: {
        url: tagAutoCompleteUrl,
        dataType: 'json',
        delay: 250,
        cache: true,
        data: function(params) {
          return {
            q: params.term
          };
        }
      },
      escapeMarkup: function (markup) { return markup; },  // Allow markup in our template.
      templateResult: function(item) {
        return '<div>' + item.text + '</div>';
      },
      minimumInputLength: 2
    });
  });

  // Initialize other select boxes.

  //$('select')
  //  .not('.field-assignees')
  //  .not('.field-do_not_assign_to')
  //  .not('.field-do_not_assign_with')
  //  .select2();

  // Initialize date fields.

  $('.widget-dateinput').datepicker({
    format: 'mm/dd/yyyy',
    assumeNearbyYear: true,
    autoclose: true
  });

  // Initialize tooltips.

  $('[data-toggle="tooltip"]').tooltip();

  // Initialize fileinputs.

  $('.widget-fileuploadwidget').on('change', function() {
    var input = $(this);
    var fileName = input.val().replace(/\\/g, '/').replace(/.*\//, '');
    input.parent().siblings('.file-upload-path').text(fileName);
  });
});
