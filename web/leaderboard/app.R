library(shiny)
library(DBI)

con = dbConnect(RPostgres::Postgres(),
                dbname = Sys.getenv('WALL_E_DB_DBNAME'),
                host = 'db',
                port = 5432,
                user = Sys.getenv('WALL_E_DB_USER'),
                password = Sys.getenv('WALL_E_DB_PASSWORD'),
                bigint = 'character')

ui = fluidPage(
    titlePanel("CSSS Discord Leaderboard"),
    fluidRow(column(12,dataTableOutput('table')))
)

server = function(input, output, session) {
    res = dbSendQuery(con, 'SELECT user_id, message_count, points, level_number FROM "WalleModels_userpoint" ORDER BY points DESC')
    df = dbFetch(res)
    dbClearResult(res)
    names(df)[names(df) == 'user_id'] = 'User ID'
    names(df)[names(df) == 'message_count'] <- 'Message count'
    names(df)[names(df) == 'points'] <- 'Points'
    names(df)[names(df) == 'level_number'] <- 'Level number'
    output$table = renderDataTable(df,options = list(pageLength = 100))
}

shinyApp(ui = ui, server = server)
