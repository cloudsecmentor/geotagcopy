library(tidyverse)
library(progress)

####### testing
mm.file <- "../data/media_metadata.csv"
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

## add author, date and GPS cooords
mm.auth.date.gps <-
  media_metadata %>%
  mutate (cust.author = map_chr(SourceFile, fun_author_SourceFile))%>%
  mutate (cust.MediaDate = parse_datetime(`File:FileModifyDate`, "%Y:%m:%d %H:%M:%S %z")) %>%
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
mm.file %>%
  str_replace("\\.csv", 
              str_c("-recs-",format(Sys.time(), "%Y-%m-%d-%H-%M-%S"), ".csv"))

mm.auth.date.gps.recs.out %>%
  write_csv(out.file.name)

# 
# ################ 
# ## fix error
# 
# 
# 
# mm.auth.date.gps  %>%
#   mutate (df = list(mm.auth.date.gps)) %>%
#   filter(is.na(cust.GPSLatt)) %>%
#   mutate ( sugg = pmap(. ,  fun_suggest_gps))
# 
# 
# a <-
#   mm.auth.date.gps  %>%
#   select_at((vars(matches("suggested|SourceFile|cust\\.")))) %>%
#   slice_head(n = 5)
# 
# a  %>%
#   select_at((vars(matches("suggested|SourceFile|cust\\.")))) %>%
#   slice_head(n = 5) %>%
#   mutate (df = list(a)) %>%
#   mutate ( sugg = ifelse( is.na(cust.GPSLatt), 
#                           pmap(. ,  fun_suggest_gps),
#                           NA)) %>%
#   unnest(sugg) %>%
#   select (-df) %>%
#   view()
# 
# 
# SourceFile <-  "/Users/sergey/Pictures/iPhone Sergey/DCIM/116APPLE/IMG_6114.JPG"
# cust.author <- "authS"
# # cust.MediaDate 
# 
# 
# 
# 
# a %>% filter (SourceFile == SourceFile)
# 
# 
#   mutate (df = list(mm.auth.date.gps)) %>%
#   filter(is.na(cust.GPSLatt)) %>%
#   mutate ( sugg = pmap(. ,  fun_suggest_gps))
#   
# 
# 
# mm.auth.date.gps.recs <-
# mm.auth.date.gps %>%
#   mutate (df = list(mm.auth.date.gps)) %>%
#   mutate ( sugg = ifelse( is.na(cust.GPSLatt), 
#                           pmap(. ,  fun_suggest_gps),
#                           NA)) %>%
#   unnest(sugg) %>%
#   select (-df) 
# 
# 
# mm.auth.date.gps.recs %>%
#   select_at(vars(matches("suggested|SourceFile|cust\\.")))
# 
# mm.file %>%
#   str_replace("\\.csv", "-recs.csv")
# 
# 
# #########################
# ##exploration
# 
# 
# 
# df <-
# mm.auth.date.gps %>%
#   select(
#     mm.auth.date.gps %>%
#       names() %>%
#       str_subset("SourceFile|cust")
#   ) %>%
#   arrange( cust.MediaDate ) 
# 
# 
# tmp.SourceFile <- "/Users/sergey/Pictures/iPhone X (S)/IMG_4180.JPG"
# tmp.sc.file <-
#   df %>%
#   filter(SourceFile == tmp.SourceFile)
# 
# tmp.cust.MediaDate <- tmp.sc.file[["cust.MediaDate"]][[1]]
# tmp.cust.author <- tmp.sc.file[["cust.author"]][[1]]
# 
# 
# 
# df %>%
#   filter ( !is.na(cust.GPSLatt)) %>%
#   filter (cust.author == tmp.cust.author) %>%
#   mutate ( time.diff =  abs (cust.MediaDate - tmp.cust.MediaDate)) %>%
#   arrange ( time.diff ) %>%
#   slice_head(n = 1) %>%
#   rename( 
#     suggested.SourceFile = SourceFile, 
#     suggested.cust.GPSLatt = cust.GPSLatt,
#     suggested.cust.GPSLong = cust.GPSLong,
#     suggested.cust.GPSAlt = cust.GPSAlt
#     ) %>% view()
#   select_at(vars(starts_with("suggested")))
# 
# 
# 
# 
# fun_suggest_gps <- function (SourceFile, cust.MediaDate, cust.author, df, ...) {
#   pb$tick()
#   tmp.cust.author <- cust.author
#   tmp.cust.MediaDate <- cust.MediaDate
#   
#   df %>%
#     filter ( !is.na(cust.GPSLatt)) %>%
#     filter (cust.author == tmp.cust.author) %>%
#     mutate ( time.diff =  abs (difftime(cust.MediaDate, tmp.cust.MediaDate, units = "hours"))) %>%
#     arrange ( time.diff ) %>%
#     slice_head(n = 1) %>%
#     rename( 
#       suggested.SourceFile = SourceFile, 
#       suggested.cust.GPSLatt = cust.GPSLatt,
#       suggested.cust.GPSLong = cust.GPSLong,
#       suggested.cust.GPSAlt = cust.GPSAlt
#     ) %>%
#     select_at(vars(matches("suggested|time.diff")))
#   
# }
# 
# fun_suggest_gps (
#                  SourceFile = tmp.SourceFile, 
#                  cust.MediaDate = tmp.cust.MediaDate, 
#                  cust.author = tmp.cust.author, 
#                  df
#                  )
# 
# #a <-
# 
# pb <- progress_bar$new(total = 200)
# 
# mm.auth.date.gps %>%
#   filter (is.na(cust.GPSLatt)) %>%
#   select_at(vars(matches("SourceFile|cust\\."))) %>%
#   slice_sample (n = 200) %>%
#   
#   mutate (df = list(mm.auth.date.gps)) %>%
#   mutate ( sugg = pmap(. ,  fun_suggest_gps) ) %>%
#   unnest(sugg) %>%
#   select (-df) 
# 
# 
# mm.gps <-
#   media_meta-data %>%
#   select(
#     media_metadata %>%
#       names() %>%
#       str_subset("SourceFile|GPS")
#   )
# 
# ## not use ICC_Profile:ProfileDateTime
# ## we will be using File:FileModificationDate
# 
# media_metadata %>%
#   select(
#     media_metadata %>%
#       names() %>%
#       str_subset("SourceFile|File:FileModifyDate")
#   ) %>%
#   mutate (MediaDate = parse_datetime(`File:FileModifyDate`, "%Y:%m:%d %H:%M:%S %z")) 
# 
# 
# 
# mm.gps <-
#   media_metadata %>%
#   select(
#     media_metadata %>%
#       names() %>%
#       str_subset("SourceFile|GPS")
#   )
# 
# 
# media_metadata %>%
#   names() %>%
#   str_subset("SourceFile|EXIF:Model")
# # str_subset("SourceFile|GPSLat|`EXIF:Model`")
# 
# 
# 
# 
# fun_filter_param <- function (param, mm.auth,...) {
#   mm.auth %>%
#     select(SourceFile, .data[[param]]) %>%
#     filter(!is.na(.data[[param]])) %>%
#     mutate(type = param,
#            value = as.character( .data[[param]])) %>%
#     slice_head(n = 3)
# }
# 
# 
# tmp <-
# mm.auth %>%
#   names() %>%
#   str_subset("GPS") %>%
#   map(fun_filter_param, mm.auth)
# 
# # tmp %>% 
# #   map_dfr(bind_rows) %>%
# #   count(SourceFile) %>%
# #   select(-n)
# # 
# 
# media_metadata %>%
#   select(
#     media_metadata %>%
#       names() %>%
#       str_subset("SourceFile|GPS")
#   ) %>%
#   right_join(
#     tmp %>% 
#       map_dfr(bind_rows) %>%
#       count(SourceFile) %>%
#       select(-n)
#   )%>%
#   view()
# 
# ##### looks like `Composite:GPSPosition` is available in all files
# 
# media_metadata %>%
#   select(
#     media_metadata %>%
#       names() %>%
#       str_subset("SourceFile|Composite:GPS(P|L|A)")
#   ) %>%
#   mutate(GPSAlt = `Composite:GPSAltitude`) %>%
#   separate(`Composite:GPSPosition`, into = c("GPSLatt", "GPSLong"), sep = " ") %>% view()
# 
# 
# # %>%
# #  filter(str_detect(SourceFile, "MOV")) %>%
#   arrange(-`Composite:GPSAltitude`)
# 
# Latt Long
# media_metadata %>%
#   
# 
#   select(SourceFile, type, date) %>%
#   pivot_wider(names_from = type, values_from = date) 
#   
# 
# media_metadata %>%
#   filter(is.na(`File:FileModifyDate`))
# 
# #################################
# 
#   unlist() %>%
#   as_tibble()
# 
# 
# tmp2 <-tibble(SourceFile = NA)
# 
# tmp %>%
#   lag(n = 1)
# 
# tmp2 %>%
#   full_join(tmp[[1]]) %>%
#   full_join(tmp[[2]])
# 
# tmp[[1]]
# 
# 
# param <- "XMP:CreateDate"
# 
# fun_filter_date (param, mm.auth)
# 
# 
# vars <- c("mass", "height")
# cond <- c(80, 150)
# starwars %>%
#   filter(
#     .data[[vars[[1]]]] > cond[[1]],
#     .data[[vars[[2]]]] > cond[[2]]
#   )
# 
# 
# mm.auth %>%
#   filter(!is.na(!!date.param))
#     
#     enquo(date.param)))
# 
# 
# #########
# 
# media_metadata %>%
#   select (
#     media_metadata %>%
#       names() %>%
#       str_subset("SourceFile|EXIF:Model")
#   ) %>%
#   mutate (author = map_chr(SourceFile, fun_author_SourceFile)) %>%
#   count(author)
# 
# 
