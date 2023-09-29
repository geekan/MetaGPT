def check_if_file_exists(curr_file): 
  """
  Checks if a file exists
  ARGS:
    curr_file: path to the current csv file. 
  RETURNS: 
    True if the file exists
    False if the file does not exist
  """
  try: 
    with open(curr_file) as f_analysis_file: pass
    return True
  except: 
    return False