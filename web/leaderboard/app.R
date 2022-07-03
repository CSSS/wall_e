library(shiny)
library(DBI)

con = dbConnect(RPostgres::Postgres(),
                dbname = Sys.getenv('WALL_E_DB_DBNAME'),
                host = 'db',
                port = 5432,
                user = Sys.getenv('WALL_E_DB_USER'),
                password = Sys.getenv('WALL_E_DB_PASSWORD'),
                bigint = 'character')

update_users = function() {
    system('python3 /srv/shiny-server/leaderboard/users.py')
    users = read.csv('/srv/shiny-server/leaderboard/users.csv',
                     colClasses = 'character')
    return(users)
}

users = update_users()

ui = fluidPage(
    titlePanel('CSSS Discord Leaderboard'),
    fluidRow(
        column(12,
               textOutput('timestamp', inline = TRUE),
               actionLink('refresh', '[Refresh]'))),
    fluidRow(
        column(12,
               dataTableOutput('table')))
)

get_user_points = function() {
    res = dbSendQuery(
        con,
        'SELECT user_id, message_count, points, level_number FROM "WalleModels_userpoint" ORDER BY points DESC')
    df = dbFetch(res)
    dbClearResult(res)
    return(df)
}

get_user_names = function(df) {
    df$rank = 1:nrow(df)
    df = merge(df, users, all.x = TRUE)
    df = df[order(df$rank),]
    na_user_name = is.na(df['user_name'])
    df[na_user_name, 'user_name'] = df[na_user_name, 'user_id']
    return(df)
}

set_col_names = function(df) {
    df = df[c('rank', 'user_name', 'message_count', 'points', 'level_number')]
    names(df)[names(df) == 'rank'] = 'Rank'
    names(df)[names(df) == 'user_name'] = 'User identifier and server nickname'
    names(df)[names(df) == 'message_count'] = 'Message count'
    names(df)[names(df) == 'points'] = 'Points'
    names(df)[names(df) == 'level_number'] = 'Level number'
    return(df)
}

update_df = function() {
    df = get_user_points()
    df = get_user_names(df)
    df = set_col_names(df)
    return(df)
}

data = reactiveValues(frame = update_df(), date = date())
date_tz = Sys.timezone()

server = function(input, output, session) {
    bindEvent(observe({
        data$frame = update_df()
        data$date = date()
    }), input$refresh)
    output$table = renderDataTable(data$frame,
                                   list(columnDefs = list(list(orderable = FALSE, targets = '_all'))))
    output$timestamp = renderText(c(data$date,date_tz))
}

shinyApp(ui = ui, server = server)
