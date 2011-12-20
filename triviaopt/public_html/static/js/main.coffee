$(() ->

  current_question = null
  start_time = null
  num_right = 0
  num_wrong = 0
  next_question = null

  loadQuestion = (cb) ->
    cb = cb ? (a, b) ->
      null

    $.get "/next-question", (data) ->
      comments = data[0].fields.category[0].fields.comments or ''
      question = $("""
        <table><tr>
          <td>
          <p class="category">#{data[0].fields.category[0].fields.name}</p>
          <p class="comments">#{comments}</p>
          </td>
        </tr><tr>
          <td class="question">
            <div class="inner-clue">
              #{data[0].fields.clue}
              <br><br><small>(#{data[0].fields.category[0].fields.meta_category})</small>
            </div>
          </td>
        </tr>
        </table>
      """)
      next_question = [question, data[0].pk]
      cb(question, data[0].pk)

  displayQuestion = (question_dom, pk) ->
      current_question = pk
      $("#question").html(question_dom)
      $("#answer").val('')
      $("#answer").focus()
      start_time = new Date().getTime()
      loadQuestion()

  loadQuestion(displayQuestion)

  $("#answerform").submit (e) ->
    $.ajax("/answer-question", {
          data: {
            question_id: current_question
            answer: $("#answer").val()
          },
          success: (data) ->
            $("#answer-container").html("""
              <span class="result">#{if data.is_correct then "Correct" else "Incorrect!"}</span>
              <span class="actual-answer">#{data.correct_response}</span>
              <a href="foo" class="change-answer">(#{if data.is_correct then "Actually wrong?" else "Actually right?"})</a>
            """)
            $(".change-answer").click (e) ->
              e.preventDefault()
              $.ajax("/change-answer", { data: { answer_id: data.answer_id } })
              $(".change-answer").remove()
              return false
            displayQuestion(next_question[0], next_question[1])
      })
    false

  session_age = $(".session-info").data("age")
  if session_age > 600
    $(".new-session").easyconfirm({
        locale: {
          title: 'Session is very old.',
          button: ['No', 'Yes']
        },
      })
    $(".new-session").trigger('click')

)