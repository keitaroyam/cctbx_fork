from iotbx import parameters

def collect_values(word_iterator, lead_word):
  last_word = lead_word
  result = []
  while True:
    word = word_iterator.try_pop(settings_index=1)
    if (word is None): break
    if (word.quote_token is not None
        or (last_word.quote_token is None and last_word.value == "\\")):
      result.append(word)
    elif (word.line_number != last_word.line_number):
      word_iterator.backup()
      break
    elif (word.value != "\\" or word.quote_token is not None):
      result.append(word)
    last_word = word
  if (len(result) == 0):
    raise RuntimeError("Missing value for %s%s" % (
      str(lead_word), lead_word.where_str()))
  return result

def collect_objects(
      word_iterator,
      definition_type_names,
      stop_token=None,
      start_word=None):
  objects = []
  while True:
    word = word_iterator.try_pop_unquoted()
    if (word is None): break
    if (stop_token is not None and word.value == stop_token):
      return objects
    lead_word = word
    if (lead_word.value == "{"):
      raise RuntimeError(
        'Syntax error: unexpected "{"%s' % lead_word.where_str())
    word = word_iterator.pop()
    if (word.quote_token is None
        and (word.value == "{"
          or (word.line_number != lead_word.line_number
              and word.value[:1] == "."))):
      if (not parameters.is_standard_identifier(lead_word.value)):
        lead_word.raise_syntax_error("improper scope name ")
      scope = parameters.scope(name=lead_word.value, objects=None)
      while True:
        if (word.value[:1] == "{"):
          break
        if (not scope.has_attribute_with_name(word.value[1:])):
          raise RuntimeError(
            "Unexpected scope attribute: %s%s" % (
              word.value, word.where_str()))
        word_iterator.pop_unquoted().assert_expected("=")
        scope.assign_attribute(
          name=word.value[1:],
          value_words=collect_values(word_iterator, word))
        word = word_iterator.pop_unquoted()
      scope.objects = collect_objects(
        word_iterator=word_iterator,
        definition_type_names=definition_type_names,
        stop_token="}",
        start_word=word)
      objects.append(scope)
    else:
      word_iterator.backup()
      if (lead_word.value[:1] != "."):
        if (not parameters.is_standard_identifier(lead_word.value)):
          lead_word.raise_syntax_error("improper definition name ")
        if (lead_word.value != "include"):
          word_iterator.pop_unquoted().assert_expected("=")
        objects.append(parameters.definition(
          name=lead_word.value,
          values=collect_values(word_iterator, lead_word)))
      else:
        if (len(objects) == 0
            or not isinstance(objects[-1], parameters.definition)
            or not objects[-1].has_attribute_with_name(lead_word.value[1:])):
          raise RuntimeError("Unexpected definition attribute: %s%s" % (
            lead_word.value, lead_word.where_str()))
        word = word_iterator.pop_unquoted()
        word.assert_expected("=")
        objects[-1].assign_attribute(
          name=lead_word.value[1:],
          value_words=collect_values(word_iterator, lead_word),
          type_names=definition_type_names)
  if (stop_token is not None):
    if (start_word is None):
      where = ""
    else:
      where = start_word.where()
    if (where == ""):
      raise RuntimeError('Syntax error: missing "%s"' % stop_token)
    raise RuntimeError('Syntax error: no matching "%s" for "%s" at %s' %
      (stop_token, str(start_word), where))
  return objects
