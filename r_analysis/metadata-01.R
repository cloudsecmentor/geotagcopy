library(tidyverse)
library(progress)

####### testing
mm.file <- "../data/2307/media_metadata_2023-07-15-01-18-01.csv"
####### testing


parse_named_args <- function(arg_names) {
  args <- commandArgs(trailingOnly = TRUE)
  named_args <- setNames(as.list(rep(NA, length(arg_names))), arg_names)
  
    if (length(args) == 0 || (length(args) == 1 && args[1] == "--help")) {
      cat("Usage: Rscript script_name.R --file <path_to_csv_file>\n")
      cat("\n")
      cat("Arguments:\n")
      for (arg_name in arg_names) {
        cat(paste0("  --", arg_name, " value\n"))
      }
      cat("\n")
      quit(save = "no", status = 0)
    }
    
  for (i in seq_along(args)) {
    if (substr(args[i], 1, 2) == "--") {
      arg_name <- substr(args[i], 3, nchar(args[i]))
      if (!(arg_name %in% arg_names)) {
        stop(paste0("Invalid argument name: ", arg_name))
      }
      named_args[[arg_name]] <- args[i+1]
    }
  }
  return(named_args)
}

# parse arguments
arg_names <- c("file")
named_args <- parse_named_args(arg_names)

# Now you can access the named arguments using their names
mm.file <- named_args[["file"]]

print (str_c("Reading data from file: ",mm.file))

# stop("Testing complete")

media_metadata <- read_csv(mm.file)


authors.regex <-
tribble(
  ~author, ~col.name, ~regex.detect, ~def.Auth,
  "authI", "SourceFile", "irina", FALSE, 
  "authT", "SourceFile", "tim", FALSE, 
  "authM", "SourceFile", "mela", FALSE, 
  "authS", "SourceFile", "serg", TRUE, 
)

fun_author_SourceFile <- function(SourceFile) {
  # function to determining who is the author of the media file
  # by the path where the file is located
  auth.filtered <-
    authors.regex %>%
    filter(str_detect(SourceFile%>%
                        str_to_lower(), 
                      regex.detect))
  
  
  if ( auth.filtered %>% nrow() > 0) {
    auth.ret <- auth.filtered[["author"]][[1]]
  } else {
    auth.ret <- authors.regex %>%
      filter(def.Auth) %>%
      pull (author)
    print("Warning: using default")
    
  }
  auth.ret
  
}

# testing:
#   "/Users/s/iPhone X (S)/IMG_5811.JPG" %>% fun_author_SourceFile()


check_missing_dates <- function(df) {
  # Subset of df where both `EXIF:DateTimeOriginal` and `QuickTime:CreateDate` are NA
  missing_date <- df %>%
    # Keep only rows where `EXIF:DateTimeOriginal` is NA
    filter(is.na(`EXIF:DateTimeOriginal`)) %>%
    # From those rows, keep only ones where `QuickTime:CreateDate` is also NA
    filter(is.na(`QuickTime:CreateDate`)) 
  
  # If there are any rows in missing_date
  if(nrow(missing_date) > 0) {
    # Issue a warning that both `EXIF:DateTimeOriginal` and `QuickTime:CreateDate` are NA
    warning("Warning: EXIF:DateTimeOriginal and QuickTime:CreateDate are NA!")
    
    # Select and return columns from missing_date that match "SourceFile" or "date"
    missing_date %>% select_at(vars(matches("SourceFile|date"))) %>% print()
  }
  else{
    # If no issues, return a message
    message("No issues found with the dates, continue..")
  }
  
}

media_metadata %>% check_missing_dates()



## add author, date and GPS cooords
mm.auth.date.gps <-
  media_metadata %>%
  mutate (cust.author = map_chr(SourceFile, fun_author_SourceFile))%>%
  mutate (cust.MediaDate = if_else(
    is.na(`EXIF:DateTimeOriginal`), 
    parse_datetime(`QuickTime:CreateDate`, "%Y:%m:%d %H:%M:%S") ,
    parse_datetime(`EXIF:DateTimeOriginal`, "%Y:%m:%d %H:%M:%S") 
  ))  %>%
  mutate(cust.GPSAlt = `Composite:GPSAltitude`) %>%
  separate(`Composite:GPSPosition`, into = c("cust.GPSLatt", "cust.GPSLong"), sep = " ")

## add recommendations for gps

### function to suggest
fun_suggest_gps <- function (SourceFile, cust.MediaDate, cust.author, df, ...) {
  pb$tick()
  tmp.cust.author <- cust.author
  tmp.cust.MediaDate <- cust.MediaDate
  
  df %>%
    filter ( !is.na(cust.GPSLatt)) %>%
    filter (cust.author == tmp.cust.author) %>%
    mutate ( suggested.time.diff =  abs (difftime(cust.MediaDate, tmp.cust.MediaDate, units = "hours"))) %>%
    arrange ( suggested.time.diff ) %>%
    slice_head(n = 1) %>%
    rename( 
      suggested.SourceFile = SourceFile, 
      suggested.cust.MediaDate = cust.MediaDate, 
      suggested.cust.GPSLatt = cust.GPSLatt,
      suggested.cust.GPSLong = cust.GPSLong,
      suggested.cust.GPSAlt = cust.GPSAlt
    ) %>%
    select_at(vars(matches("suggested")))
  
}

### recommedations

print("found authors:")
mm.auth.date.gps %>%
  select_at(vars(matches("suggested|SourceFile|cust\\.")))%>%
  mutate (df = list(mm.auth.date.gps)) %>%
  count(cust.author)

### progress bar
pb <- progress_bar$new(total = nrow(mm.auth.date.gps))
# recs
mm.auth.date.gps.recs <-
  mm.auth.date.gps %>% 
  mutate (df = list(mm.auth.date.gps)) %>%
  mutate ( sugg = ifelse( is.na(cust.GPSLatt), 
                          pmap(. ,  fun_suggest_gps),
                          NA)) %>%
  unnest(sugg) %>%
  select (-df) 

mm.auth.date.gps.recs.out <-
mm.auth.date.gps.recs %>%
  select_at(vars(matches("suggested|SourceFile|cust\\.")))



out.file.name <-
mm.file 
## using the same file name!!!
# %>%
#   str_replace("\\.csv", 
#               str_c("-recs-",format(Sys.time(), "%Y-%m-%d-%H-%M-%S"), ".csv"))

mm.auth.date.gps.recs.out %>%
  write_csv(out.file.name)


# #################################
